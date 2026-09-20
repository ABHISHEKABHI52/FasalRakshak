"""Scan, image asset and image-quality result (docs/07 §3, docs/00 §27.1–27.2).

Scan lifecycle (docs/07 vocabulary + explicit quality-gate states required by the
Phase 2 pipeline contract — see docs/IMPLEMENTATION_STATUS.md for the mapping):

    PENDING_IMAGE      documented — scan created, no image yet
    QUALITY_CHECKING   additive    — quality gate running (transient)
    QUALITY_REJECTED   additive    — gate failed; NO analysis is run
    ANALYZING          documented — image accepted, analysis step running
    COMPLETED          documented — pipeline finished (outcome may still be
                                     "insufficient evidence" via diagnoses.final_status)
    FAILED             documented — analysis error, retryable

`insufficient_evidence` is a DIAGNOSIS outcome (docs/07 §4), not a scan state —
that keeps "we do not know" separate from "processing failed".
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType, TimestampMixin, UUIDPkMixin, UpdatedAtMixin
from app.models.crop import portable_enum

ALLOWED_IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")


class ScanStatus(str, enum.Enum):
    # Values follow docs/07 §3 (pending_image|analyzing|completed|failed) plus the
    # explicit quality-gate states required by the Phase 2 pipeline contract.
    PENDING_IMAGE = "pending_image"
    QUALITY_CHECKING = "quality_checking"
    QUALITY_REJECTED = "quality_rejected"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class PlantPart(str, enum.Enum):
    # Values match docs/07 §3 (leaf/stem/fruit/whole_plant/trap).
    LEAF = "leaf"
    STEM = "stem"
    FRUIT = "fruit"
    WHOLE_PLANT = "whole_plant"
    TRAP = "trap"


class QualityCategory(str, enum.Enum):
    # Values match docs/07 §3 (good|acceptable|poor|unusable).
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    UNUSABLE = "unusable"


class ImageAsset(Base, UUIDPkMixin, TimestampMixin):
    """Stored image metadata. Binary lives in the media store; this row is metadata only."""

    __tablename__ = "images"
    __table_args__ = (CheckConstraint("size_bytes > 0", name="size_positive"),)

    storage_path: Mapped[str] = mapped_column(Text, nullable=False)  # server-generated key
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(40), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)


class CropScan(Base, UUIDPkMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "crop_scans"
    __table_args__ = (
        Index("ix_crop_scans_field_created", "field_id", "created_at"),
        Index("ix_crop_scans_status", "status"),
    )

    client_scan_uuid: Mapped[uuid.UUID] = mapped_column(Uuid(), unique=True, nullable=False)
    field_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False
    )
    crop_cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("crop_cycles.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    plant_part: Mapped[str] = mapped_column(portable_enum(PlantPart, "plant_part"), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("images.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        portable_enum(ScanStatus, "scan_status"), default=ScanStatus.PENDING_IMAGE, nullable=False
    )
    # Explicit machine-readable failure/insufficiency context; never a stack trace.
    status_reason: Mapped[str | None] = mapped_column(String(60), nullable=True)

    image: Mapped[ImageAsset | None] = relationship(lazy="selectin")
    quality_result: Mapped["ImageQualityResult | None"] = relationship(
        back_populates="scan", lazy="selectin", uselist=False
    )
    diagnosis: Mapped["Diagnosis | None"] = relationship(  # type: ignore[name-defined]
        lazy="selectin", uselist=False
    )


class ImageQualityResult(Base, UUIDPkMixin, TimestampMixin):
    """1:1 with a scan (docs/07 §3). Thresholds/weights are PROTOTYPE constants (docs/00 §16)."""

    __tablename__ = "image_quality_results"
    __table_args__ = (CheckConstraint("quality_score BETWEEN 0 AND 100", name="score_range"),)

    scan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("crop_scans.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    quality_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    category: Mapped[str] = mapped_column(
        portable_enum(QualityCategory, "quality_category"), nullable=False
    )
    reasons: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    leaf_coverage: Mapped[float | None] = mapped_column(Float, nullable=True)
    usable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    model_ref: Mapped[str | None] = mapped_column(String(40), nullable=True)

    scan: Mapped[CropScan] = relationship(back_populates="quality_result")

    