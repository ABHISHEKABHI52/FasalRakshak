"""Scan lifecycle + image pipeline (docs/03 FR-C/FR-D, docs/08 §3, docs/13 Flow A).

Phase 2 implements: create (idempotent) → upload/validate → quality gate → analysis
contract → outcome. The disease model itself is NOT part of this phase, so the
default analysis service returns INSUFFICIENT_EVIDENCE (an honest, first-class outcome).
"""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.service import AnalysisContext, AnalysisStatus, ImageAnalysisService
from app.core.config import get_settings
from app.core.errors import (
    ConflictError,
    NotFoundError,
    QualityUnusableError,
    ServiceUnavailableError,
)
from app.models.diagnosis import DiagnosisStatus
from app.models.scan import CropScan, ScanStatus
from app.quality.engine import assess_image
from app.quality.validation import decode_upload
from app.repositories.crop_cycle_repository import CropCycleRepository
from app.repositories.crop_repository import CropRepository
from app.repositories.field_repository import FieldRepository
from app.repositories.image_repository import DiagnosisRepository, ImageRepository
from app.repositories.scan_repository import ScanRepository
from app.schemas.scan import (
    AnalysisSummary,
    ImageSummary,
    ImageUploadResponse,
    QualitySummary,
    ScanCreatedResponse,
    ScanCreate,
    ScanListResponse,
    ScanResponse,
)
from app.services.audit_service import AuditService
from app.storage.local import LocalImageStore

ALLOWED_UPLOAD_STATES = {ScanStatus.PENDING_IMAGE, ScanStatus.QUALITY_REJECTED, ScanStatus.FAILED}


def _enum_value(value) -> str:  # type: ignore[no-untyped-def]
    return value.value if hasattr(value, "value") else str(value)


class ScanService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        analysis_service: ImageAnalysisService,
        image_store: LocalImageStore,
    ) -> None:
        self.session = session
        self.scans = ScanRepository(session)
        self.fields = FieldRepository(session)
        self.cycles = CropCycleRepository(session)
        self.crops = CropRepository(session)
        self.images = ImageRepository(session)
        self.diagnoses = DiagnosisRepository(session)
        self.audit = AuditService(session)
        self.analysis_service = analysis_service
        self.image_store = image_store
        self.settings = get_settings()

    # ---------- response builders ----------

    @staticmethod
    def _quality_summary(result) -> QualitySummary:  # type: ignore[no-untyped-def]
        payload = result.reasons or {}
        return QualitySummary(
            quality_score=result.quality_score,
            category=result.category,
            usable=result.usable,
            leaf_coverage=result.leaf_coverage,
            reasons=payload.get("items", []),
            metrics=payload.get("metrics"),
            model_ref=result.model_ref,
        )

    @staticmethod
    def _analysis_summary(diagnosis) -> AnalysisSummary | None:  # type: ignore[no-untyped-def]
        if diagnosis is None:
            return None
        trace = diagnosis.evidence_trace or []
        return AnalysisSummary(
            status=_enum_value(diagnosis.final_status),
            primary_label_code=diagnosis.primary_label_code,
            confidence=diagnosis.fused_confidence,
            candidates=diagnosis.differential or [],
            reasons=[item["reason"] for item in trace if isinstance(item, dict) and item.get("reason")],
            model_name=diagnosis.analysis_model,
            is_mock=diagnosis.is_mock,
            note=diagnosis.note,
        )

    def to_response(self, scan: CropScan) -> ScanResponse:
        return ScanResponse(
            id=scan.id,
            client_scan_uuid=scan.client_scan_uuid,
            field_id=scan.field_id,
            crop_cycle_id=scan.crop_cycle_id,
            plant_part=scan.plant_part,
            captured_at=scan.captured_at,
            status=scan.status,
            status_reason=scan.status_reason,
            created_at=scan.created_at,
            updated_at=scan.updated_at,
            image=ImageSummary.model_validate(scan.image) if scan.image else None,
            quality=self._quality_summary(scan.quality_result) if scan.quality_result else None,
            analysis=self._analysis_summary(scan.diagnosis),
        )

    # ---------- scan creation & reads ----------

    async def create_scan(
        self, owner_id: uuid.UUID, data: ScanCreate
    ) -> tuple[ScanCreatedResponse, bool]:
        """Returns (response, created). created=False means an idempotent replay (docs/08 §3)."""
        existing = await self.scans.get_by_client_uuid(data.client_scan_uuid)
        if existing is not None:
            if existing.user_id != owner_id:
                # Another farmer's key — never reveal that the scan exists.
                raise NotFoundError(details={"resource": "scan"})
            return ScanCreatedResponse(scan_id=existing.id, status=existing.status), False

        if await self.fields.get_for_owner(data.field_id, owner_id) is None:
            raise NotFoundError(details={"resource": "field"})
        cycle_row = await self.cycles.get_for_owner(data.crop_cycle_id, owner_id)
        if cycle_row is None:
            raise NotFoundError(details={"resource": "crop_cycle"})
        if cycle_row[0].field_id != data.field_id:
            # Cycle must belong to the scanned field — prevents cross-field mixups.
            raise ConflictError(
                code="cycle_field_mismatch", message_key="errors.cycle_field_mismatch"
            )

        scan = await self.scans.create(
            client_scan_uuid=data.client_scan_uuid,
            field_id=data.field_id,
            crop_cycle_id=data.crop_cycle_id,
            user_id=owner_id,
            plant_part=data.plant_part,
            captured_at=data.captured_at,
        )
        await self.audit.record(
            action="scan.create",
            resource_type="crop_scan",
            resource_id=scan.id,
            user_id=owner_id,
            after={"status": ScanStatus.PENDING_IMAGE.value, "field_id": str(data.field_id)},
        )
        return ScanCreatedResponse(scan_id=scan.id, status=scan.status), True

    async def get_scan(self, scan_id: uuid.UUID, owner_id: uuid.UUID) -> ScanResponse:
        scan = await self.scans.get_for_owner(scan_id, owner_id)
        if scan is None:
            raise NotFoundError(details={"resource": "scan"})
        return self.to_response(scan)

    async def list_scans(
        self,
        owner_id: uuid.UUID,
        *,
        field_id: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int = 20,
    ) -> ScanListResponse:
        if field_id is not None and await self.fields.get_for_owner(field_id, owner_id) is None:
            raise NotFoundError(details={"resource": "field"})
        items, next_cursor = await self.scans.list_for_owner(
            owner_id, field_id=field_id, cursor=cursor, limit=limit
        )
        return ScanListResponse(
            items=[self.to_response(scan) for scan in items], next_cursor=next_cursor
        )

    # ---------- image upload pipeline ----------

    async def upload_image(
        self, scan_id: uuid.UUID, owner_id: uuid.UUID, *, data: bytes, filename: str | None
    ) -> ImageUploadResponse:
        """Validate → decode → quality gate → analysis contract (docs/13 Flow A)."""
        scan = await self.scans.get_for_owner(scan_id, owner_id)
        if scan is None:
            raise NotFoundError(details={"resource": "scan"})
        if scan.status not in ALLOWED_UPLOAD_STATES:
            raise ConflictError(
                code="image_already_accepted", message_key="errors.image_already_accepted"
            )

        # 1) Never trust the client: size cap + real format detection + safe decode.
        image, _detected_mime = decode_upload(
            data,
            max_bytes=self.settings.MAX_UPLOAD_BYTES,
            max_pixels=self.settings.MAX_IMAGE_PIXELS,
        )
        await self.scans.set_status(scan, ScanStatus.QUALITY_CHECKING)

        # 2) Store the re-encoded image (server-generated key; EXIF and payloads dropped).
        checksum = hashlib.sha256(data).hexdigest()
        image_asset = await self.images.find_by_checksum(checksum)
        if image_asset is None:
            storage_key, size_bytes, width, height = self.image_store.save_scan_image(
                image,
                scan_id=scan.id,
                max_dimension=self.settings.STORED_IMAGE_MAX_DIMENSION,
                jpeg_quality=self.settings.STORED_IMAGE_JPEG_QUALITY,
            )
            image_asset = await self.images.create_image(
                storage_path=storage_key,
                original_filename=safe_filename(filename),
                mime_type="image/jpeg",
                size_bytes=size_bytes,
                width=width,
                height=height,
                checksum_sha256=checksum,
            )
        scan.image_id = image_asset.id
        scan.image = image_asset  # keep the relationship in memory (never lazy-load in async paths)

        # 3) Quality gate (prototype heuristics — docs/00 §16).
        assessment = assess_image(
            image,
            min_dimension=self.settings.MIN_IMAGE_DIMENSION,
            band_good=self.settings.QUALITY_BAND_GOOD_MIN,
            band_acceptable=self.settings.QUALITY_BAND_ACCEPTABLE_MIN,
            band_poor=self.settings.QUALITY_BAND_POOR_MIN,
        )
        await self._persist_quality(scan, image_asset.id, assessment)
        await self.audit.record(
            action="scan.image_upload",
            resource_type="crop_scan",
            resource_id=scan.id,
            user_id=owner_id,
            after={
                "quality_score": assessment.quality_score,
                "category": assessment.category.value,
                "usable": assessment.usable,
            },
        )

        # 4) Unusable → NO analysis is attempted (docs/03 AC-01, docs/00 §16).
        if not assessment.usable:
            await self.scans.set_status(
                scan, ScanStatus.QUALITY_REJECTED, reason="image_quality_unusable"
            )
            await self._record_outcome(
                scan,
                status=AnalysisStatus.INSUFFICIENT_EVIDENCE,
                reasons=["image_quality_unusable"],
                model_name="quality_gate",
                assessment=assessment,
            )
            await self.session.commit()
            raise QualityUnusableError(
                details={
                    "reasons": assessment.reasons,
                    "reasons_detail": assessment.reasons_payload()["items"],
                    "quality_score": assessment.quality_score,
                    "category": assessment.category.value,
                }
            )

        # 5) Accepted → analysis contract (Phase 2 default: INSUFFICIENT_EVIDENCE).
        await self.scans.set_status(scan, ScanStatus.ANALYZING)
        outcome = await self._run_analysis(scan, owner_id)
        await self._record_outcome(
            scan,
            status=outcome.status,
            reasons=outcome.reasons,
            model_name=outcome.model_name,  # name only; version lives in the evidence trace
            assessment=assessment,
            outcome=outcome,
        )
        return ImageUploadResponse(
            scan_id=scan.id,
            image_id=image_asset.id,
            status=scan.status,
            quality=self._quality_summary(scan.quality_result),
            analysis=self._analysis_summary(scan.diagnosis),
        )

    # ---------- pipeline helpers ----------

    async def _persist_quality(self, scan: CropScan, image_id: uuid.UUID, assessment) -> None:  # type: ignore[no-untyped-def]
        """Write the 1:1 quality row (replaced when an image is re-uploaded)."""
        payload = assessment.reasons_payload()
        existing = await self.images.get_quality_for_scan(scan.id)
        if existing is None:
            existing = await self.images.create_quality_result(
                scan_id=scan.id,
                image_id=image_id,
                quality_score=assessment.quality_score,
                category=assessment.category,
                reasons=payload,
                leaf_coverage=assessment.leaf_coverage,
                usable=assessment.usable,
                model_ref="heuristic-v1",
            )
        else:
            existing.image_id = image_id
            existing.quality_score = assessment.quality_score
            existing.category = assessment.category
            existing.reasons = payload
            existing.leaf_coverage = assessment.leaf_coverage
            existing.usable = assessment.usable
            existing.model_ref = "heuristic-v1"
            await self.session.flush()
        # Keep the in-memory relationship populated (never lazy-load in async context).
        scan.quality_result = existing

    async def _run_analysis(self, scan: CropScan, owner_id: uuid.UUID):  # type: ignore[no-untyped-def]
        """Invoke the analysis contract with image + crop/field/cycle context (docs/06 §8)."""
        cycle_row = await self.cycles.get_for_owner(scan.crop_cycle_id, owner_id)
        if cycle_row is None:
            raise NotFoundError(details={"resource": "crop_cycle"})
        cycle, crop = cycle_row
        field = await self.fields.get_by_id(scan.field_id)
        quality = scan.quality_result
        context = AnalysisContext(
            scan_id=scan.id,
            image_path=self.image_store.resolve(scan.image.storage_path),  # type: ignore[union-attr]
            crop_code=crop.code,
            crop_stage=_enum_value(cycle.current_stage),
            plant_part=_enum_value(scan.plant_part),
            field_id=scan.field_id,
            district=field.district_code if field is not None else None,
            quality_score=quality.quality_score if quality else 0,
            quality_category=_enum_value(quality.category) if quality else "UNKNOWN",
        )
        try:
            return self.analysis_service.analyze(context)
        except Exception as exc:  # analysis failure is explicit, never silent (docs/39)
            await self.scans.set_status(scan, ScanStatus.FAILED, reason="analysis_failed")
            await self._record_outcome(
                scan,
                status=AnalysisStatus.INSUFFICIENT_EVIDENCE,
                reasons=["analysis_failed"],
                model_name="analysis_error",
            )
            raise ServiceUnavailableError(
                code="analysis_failed", message_key="errors.analysis_failed"
            ) from exc

    async def _record_outcome(
        self,
        scan: CropScan,
        *,
        status: AnalysisStatus,
        reasons: list[str],
        model_name: str | None = None,
        assessment=None,  # type: ignore[no-untyped-def]
        outcome=None,  # type: ignore[no-untyped-def]
    ) -> None:
        """Persist the outcome row; INSUFFICIENT_EVIDENCE is a valid terminal state (docs/06 §9)."""
        differential = (
            [
                {"label_code": candidate.label_code, "confidence": candidate.confidence}
                for candidate in outcome.candidates
            ]
            if outcome is not None
            else []
        )
        trace: list[dict] = []
        for reason in reasons:
            entry: dict = {"reason": reason}
            if assessment is not None:
                entry["quality_score"] = assessment.quality_score
                entry["quality_category"] = assessment.category.value
            trace.append(entry)
        if outcome is not None:
            trace.append(
                {
                    "model": f"{outcome.model_name}:{outcome.model_version}",
                    "inference_ms": outcome.inference_ms,
                    "is_mock": outcome.is_mock,
                }
            )
        diagnosis = await self.diagnoses.upsert_for_scan(
            scan_id=scan.id,
            final_status=(
                DiagnosisStatus.DIAGNOSED
                if status is AnalysisStatus.DIAGNOSED
                else DiagnosisStatus.INSUFFICIENT_EVIDENCE
            ),
            primary_label_code=outcome.primary_label_code if outcome is not None else None,
            fused_confidence=outcome.confidence if outcome is not None else None,
            differential=differential,
            evidence_trace=trace,
            analysis_model=model_name,
            is_mock=bool(outcome.is_mock) if outcome is not None else False,
            note=_outcome_note(reasons, outcome),
        )
        scan.diagnosis = diagnosis
        if scan.status in {ScanStatus.ANALYZING, ScanStatus.QUALITY_CHECKING}:
            await self.scans.set_status(
                scan, ScanStatus.COMPLETED, reason=reasons[0] if reasons else None
            )
        else:
            scan.status_reason = reasons[0] if reasons else None
            await self.session.flush()


def safe_filename(filename: str | None) -> str | None:
    """Keep only a harmless display name — never a path (docs/12 §3)."""
    if not filename:
        return None
    cleaned = filename.replace("\\", "/").split("/")[-1].strip()
    cleaned = "".join(ch for ch in cleaned if ch.isprintable())[:255]
    return cleaned or None


def _outcome_note(reasons: list[str], outcome) -> str | None:  # type: ignore[no-untyped-def]
    if outcome is not None and outcome.is_mock:
        return "TEST double inference — NOT a real model prediction."
    if "image_quality_unusable" in reasons:
        return "Image failed the quality gate; no analysis was run."
    if "analysis_failed" in reasons:
        return "The analysis step failed; this scan can be retried."
    if "analysis_model_unavailable" in reasons:
        return "No disease model is deployed yet (Phase 3); outcome recorded as insufficient evidence."
    return None