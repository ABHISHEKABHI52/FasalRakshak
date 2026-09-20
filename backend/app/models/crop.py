"""Crop catalogue, crop cycles + shared geospatial/enum column types (docs/07 §2).

Field location is PostGIS `geography(Point,4326)` on PostgreSQL (GIST indexed).
GeoPointType keeps the same models usable on SQLite for tests/dev by falling back
to WKT text — the SQLite path is a test-only approximation (see IMPLEMENTATION_STATUS).
"""

import enum
import uuid
from datetime import date, datetime

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.db.base import Base, JSONType, TimestampMixin, UUIDPkMixin, UpdatedAtMixin


class GeoPointType(TypeDecorator):
    """geography(Point,4326) on PostgreSQL; WKT text elsewhere (SQLite tests)."""

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Geography(geometry_type="POINT", srid=4326))
        return dialect.type_descriptor(Text())


class CropStage(str, enum.Enum):
    # Values match docs/07 §2 (seedling/vegetative/flowering/fruiting/maturity).
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    FLOWERING = "flowering"
    FRUITING = "fruiting"
    MATURITY = "maturity"


class CycleStatus(str, enum.Enum):
    # Values match docs/07 §2 (active/completed/abandoned).
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


def portable_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """VARCHAR + CHECK in both dialects (docs/07 — no native enum types)."""
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=lambda e: [m.value for m in e],
        native_enum=False,
    )


class Crop(Base, UUIDPkMixin, TimestampMixin):
    """Controlled crop catalogue — free-text crop names are not accepted (docs/00 §27.1)."""

    __tablename__ = "crops"

    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(80), nullable=False)
    name_hi: Mapped[str] = mapped_column(String(80), nullable=False)
    scientific_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Prototype stage thresholds (days since sowing) — NOT agronomically validated.
    stage_model: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    is_supported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    cycles: Mapped[list["CropCycle"]] = relationship(back_populates="crop")


class CropCycle(Base, UUIDPkMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "crop_cycles"
    __table_args__ = (Index("ix_crop_cycles_field_sowing", "field_id", "sowing_date"),)

    field_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("fields.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("crops.id", ondelete="RESTRICT"), nullable=False
    )
    variety: Mapped[str | None] = mapped_column(String(80), nullable=True)
    sowing_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    current_stage: Mapped[str] = mapped_column(
        portable_enum(CropStage, "crop_stage"), nullable=False
    )
    stage_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        portable_enum(CycleStatus, "cycle_status"), default=CycleStatus.ACTIVE, nullable=False
    )

    field: Mapped["Field"] = relationship(back_populates="cycles")  # type: ignore[name-defined]
    crop: Mapped[Crop] = relationship(back_populates="cycles")

    