"""Image asset, quality-result and diagnosis persistence (docs/07 §3–4)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.diagnosis import Diagnosis
from app.models.scan import CropScan, ImageAsset, ImageQualityResult


class ImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_checksum(self, checksum: str) -> ImageAsset | None:
        """Content-addressed dedupe (docs/07 images.checksum_sha256 UNIQUE)."""
        return (
            await self.session.execute(select(ImageAsset).where(ImageAsset.checksum_sha256 == checksum))
        ).scalar_one_or_none()

    async def create_image(
        self,
        *,
        storage_path: str,
        original_filename: str | None,
        mime_type: str,
        size_bytes: int,
        width: int,
        height: int,
        checksum_sha256: str,
    ) -> ImageAsset:
        image = ImageAsset(
            storage_path=storage_path,
            original_filename=original_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            width=width,
            height=height,
            checksum_sha256=checksum_sha256,
        )
        self.session.add(image)
        await self.session.flush()
        return image

    async def get_quality_for_scan(self, scan_id: uuid.UUID) -> ImageQualityResult | None:
        return (
            await self.session.execute(
                select(ImageQualityResult).where(ImageQualityResult.scan_id == scan_id)
            )
        ).scalar_one_or_none()

    async def create_quality_result(
        self,
        *,
        scan_id: uuid.UUID,
        image_id: uuid.UUID,
        quality_score: int,
        category: str,
        reasons: dict,
        leaf_coverage: float | None,
        usable: bool,
        model_ref: str | None,
    ) -> ImageQualityResult:
        result = ImageQualityResult(
            scan_id=scan_id,
            image_id=image_id,
            quality_score=quality_score,
            category=category,
            reasons=reasons,
            leaf_coverage=leaf_coverage,
            usable=usable,
            model_ref=model_ref,
        )
        self.session.add(result)
        await self.session.flush()
        return result


class DiagnosisRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_for_scan(self, scan_id: uuid.UUID) -> Diagnosis | None:
        return (
            await self.session.execute(select(Diagnosis).where(Diagnosis.scan_id == scan_id))
        ).scalar_one_or_none()

    async def upsert_for_scan(
        self,
        *,
        scan_id: uuid.UUID,
        final_status: str,
        primary_label_code: str | None,
        fused_confidence: float | None,
        differential: list | None,
        evidence_trace: list | None,
        analysis_model: str | None,
        is_mock: bool,
        note: str | None,
    ) -> Diagnosis:
        existing = await self.get_for_scan(scan_id)
        if existing is None:
            existing = Diagnosis(scan_id=scan_id)
            self.session.add(existing)
        existing.final_status = final_status
        existing.primary_label_code = primary_label_code
        existing.fused_confidence = fused_confidence
        existing.differential = differential
        existing.evidence_trace = evidence_trace
        existing.analysis_model = analysis_model
        existing.is_mock = is_mock
        existing.note = note
        await self.session.flush()
        return existing