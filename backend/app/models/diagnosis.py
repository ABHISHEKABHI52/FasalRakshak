"""Diagnosis outcome row (docs/07 §4) — 1:1 with a scan.

Phase 2 creates this row to record the analysis outcome, where
**`INSUFFICIENT_EVIDENCE` is a first-class, successful outcome** (docs/06 §9):
the system is allowed to say "we do not know" instead of forcing a disease name.

Phase 3 (adaptive questions, context fusion, risk) extends this row; the remaining
documented statuses are reserved for the expert-validation layer.
"""

import enum
import uuid

from sqlalchemy import Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, JSONType, TimestampMixin, UUIDPkMixin, UpdatedAtMixin
from app.models.crop import portable_enum


class DiagnosisStatus(str, enum.Enum):
    # Values match docs/07 §4 (diagnosed|insufficient_evidence|referred_expert|...).
    DIAGNOSED = "diagnosed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    REFERRED_EXPERT = "referred_expert"          # reserved (Phase 5)
    EXPERT_CONFIRMED = "expert_confirmed"        # reserved (Phase 5)
    EXPERT_CORRECTED = "expert_corrected"        # reserved (Phase 5)
    REJECTED = "rejected"                        # reserved (Phase 5)


class Diagnosis(Base, UUIDPkMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "diagnoses"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("crop_scans.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    final_status: Mapped[str] = mapped_column(
        portable_enum(DiagnosisStatus, "diagnosis_status"),
        default=DiagnosisStatus.INSUFFICIENT_EVIDENCE,
        nullable=False,
    )
    primary_label_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fused_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    differential: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    evidence_trace: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    final_label_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    # Which analysis contract produced this outcome (model name/version or "unavailable").
    analysis_model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_mock: Mapped[bool] = mapped_column(default=False, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)