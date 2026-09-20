"""Farm and Field entities (docs/07 §2, docs/00 §27.1)."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPkMixin, UpdatedAtMixin
from app.models.crop import CropCycle, GeoPointType


class Farm(Base, UUIDPkMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "farms"
    __table_args__ = (Index("ix_farms_owner_active", "owner_id", "is_active"),)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    fields: Mapped[list["Field"]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )


class Field(Base, UUIDPkMixin, TimestampMixin, UpdatedAtMixin):
    __tablename__ = "fields"
    __table_args__ = (Index("ix_fields_farm_active", "farm_id", "is_active"),)

    farm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    area_hectares: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    # PostGIS geography(Point,4326) on PostgreSQL (docs/07 §9); WKT text on SQLite tests.
    location: Mapped[str | None] = mapped_column(GeoPointType, nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    district_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    farm: Mapped[Farm] = relationship(back_populates="fields")
    cycles: Mapped[list[CropCycle]] = relationship(
        back_populates="field", cascade="all, delete-orphan"
    )