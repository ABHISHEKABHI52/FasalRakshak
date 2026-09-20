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


def get_analysis_service() -> ImageAnalysisService:
    """FastAPI dependency — overridden in tests to exercise the DIAGNOSED path."""
    return UnavailableImageAnalysisService()