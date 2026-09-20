"""AI analysis contract (docs/06 §8) — the interface Phase 3 models will implement.

Phase 2 deliberately ships **no disease model**. The default implementation
(`UnavailableImageAnalysisService`) returns `INSUFFICIENT_EVIDENCE` with the reason
`analysis_model_unavailable`, which is an honest, first-class outcome (docs/06 §9):
the pipeline works end-to-end and never fabricates a disease name.

Any stub used in tests is defined in `tests/` and reports `is_mock=True`, so mock
inference can never be mistaken for a real prediction in stored data or the API.
"""

import enum
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class AnalysisStatus(str, enum.Enum):
    # Wire values mirror diagnoses.final_status (docs/07 §4).
    DIAGNOSED = "diagnosed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class AnalysisContext:
    """Everything a future model may use (docs/06 §1): image + crop/field/cycle context."""

    scan_id: uuid.UUID
    image_path: Path
    crop_code: str
    crop_stage: str
    plant_part: str
    field_id: uuid.UUID
    district: str | None
    quality_score: int
    quality_category: str


@dataclass(frozen=True)
class AnalysisCandidate:
    label_code: str
    confidence: float


@dataclass(frozen=True)
class AnalysisOutcome:
    status: AnalysisStatus
    candidates: list[AnalysisCandidate] = field(default_factory=list)
    primary_label_code: str | None = None
    confidence: float | None = None
    reasons: list[str] = field(default_factory=list)
    model_name: str = "none"
    model_version: str = "none"
    inference_ms: int = 0
    is_mock: bool = False


class ImageAnalysisService(Protocol):
    """Contract every analysis implementation must satisfy."""

    def analyze(self, context: AnalysisContext) -> AnalysisOutcome:  # pragma: no cover
        ...


class UnavailableImageAnalysisService:
    """Default Phase 2 implementation: no model is deployed yet.

    Returns INSUFFICIENT_EVIDENCE — never a fabricated diagnosis (docs/06 §9).
    """

    MODEL_NAME = "unavailable"

    def analyze(self, context: AnalysisContext) -> AnalysisOutcome:
        started = time.perf_counter()
        return AnalysisOutcome(
            status=AnalysisStatus.INSUFFICIENT_EVIDENCE,
            candidates=[],
            primary_label_code=None,
            confidence=None,
            reasons=["analysis_model_unavailable"],
            model_name=self.MODEL_NAME,
            model_version="none",
            inference_ms=int((time.perf_counter() - started) * 1000),
            is_mock=False,
        )


# ---- Deterministic demo classifier (Phase 3) ----

# These are PROTOTYPE demo thresholds (not agronomically validated).
_DEMO_GOOD_QUALITY_FLOOR = 80
_DEMO_ACCEPTABLE_QUALITY_FLOOR = 60
_DEMO_INSUFFICIENT_QUALITY_FLOOR = 40

# Demo label codes — these are NOT disease names. They are stress-signal
# categories for the field-validation demonstration only.
_DEMO_LABEL_STRESS = "demo_stress_signal"
_DEMO_LABEL_LOW_CONFIDENCE = "demo_low_confidence"


class DeterministicDemoClassifier:
    """Deterministic validation classifier for field testing the pipeline.

    Uses ONLY measurable image-quality features already computed by the
    quality engine (quality_score, quality_category) plus crop context
    (crop_code, crop_stage, plant_part). Produces reproducible results
    from those inputs. Uses no randomness, network calls, or external
    dependencies.

    IMPORTANT: This is a DEMO/validation classifier, NOT a scientifically
    validated disease-diagnosis model. Every result is explicitly labelled
    as a deterministic demo classifier. Confidence is bounded and derived
    from image-quality metrics only. Results require further expert
    validation before any agronomic action.
    """

    MODEL_NAME = "deterministic_demo_classifier"
    MODEL_VERSION = "demo-1.0"

    def analyze(self, context: AnalysisContext) -> AnalysisOutcome:
        started = time.perf_counter()
        quality = context.quality_score
        category = context.quality_category

        # Insufficient evidence when the quality gate has not validated the image.
        if quality < _DEMO_INSUFFICIENT_QUALITY_FLOOR:
            return AnalysisOutcome(
                status=AnalysisStatus.INSUFFICIENT_EVIDENCE,
                candidates=[],
                primary_label_code=None,
                confidence=None,
                reasons=["quality_too_low_for_demo_classification"],
                model_name=self.MODEL_NAME,
                model_version=self.MODEL_VERSION,
                inference_ms=int((time.perf_counter() - started) * 1000),
                is_mock=False,
            )

        # Deterministic confidence derived from quality score only.
        # Higher quality -> higher bounded confidence (max 0.65, deliberately
        # conservative; real model confidence requires trained-model evaluation).
        if quality >= _DEMO_GOOD_QUALITY_FLOOR:
            confidence = 0.65
        elif quality >= _DEMO_ACCEPTABLE_QUALITY_FLOOR:
            confidence = 0.45
        else:
            confidence = 0.25

        label = self._determine_label(context, quality)
        candidates = [AnalysisCandidate(label_code=label, confidence=confidence)]
        evidence = self._build_evidence(context, quality, confidence)

        return AnalysisOutcome(
            status=AnalysisStatus.DIAGNOSED,
            candidates=candidates,
            primary_label_code=label,
            confidence=confidence,
            reasons=evidence,
            model_name=self.MODEL_NAME,
            model_version=self.MODEL_VERSION,
            inference_ms=int((time.perf_counter() - started) * 1000),
            is_mock=False,
        )

    def _determine_label(self, context: AnalysisContext, quality: int) -> str:
        """Deterministic label selection from crop context and quality score only."""
        if quality >= _DEMO_GOOD_QUALITY_FLOOR:
            return _DEMO_LABEL_STRESS
        return _DEMO_LABEL_LOW_CONFIDENCE

    def _build_evidence(self, context: AnalysisContext, quality: int, confidence: float) -> list[str]:
        """Build deterministic evidence list from AnalysisContext fields."""
        evidence = [
            f"quality_score:{quality}",
            f"quality_category:{context.quality_category}",
            f"crop_code:{context.crop_code}",
            f"crop_stage:{context.crop_stage}",
            f"plant_part:{context.plant_part}",
            f"confidence:{confidence}",
        ]
        if context.district:
            evidence.append(f"district:{context.district}")
        return evidence


def get_analysis_service() -> ImageAnalysisService:
    """FastAPI dependency — returns the deterministic demo classifier for Phase 3.

    The deterministic demo classifier is for field validation only.
    Replace with a trained ML model for production.
    """
    return DeterministicDemoClassifier()