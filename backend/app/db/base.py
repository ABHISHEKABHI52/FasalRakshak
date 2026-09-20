"""Declarative base, naming conventions and shared column mixins (docs/07 §conventions)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, DateTime, Integer, MetaData, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# JSONB on PostgreSQL (docs/07); plain JSON on SQLite (tests/dev only).
JSONType = JSONB().with_variant(JSON(), "sqlite")
# BIGINT on PostgreSQL; INTEGER on SQLite (only INTEGER autoincrements there).
BigIntType = BigInteger().with_variant(Integer(), "sqlite")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPkMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(), primary_key=True, default=new_uuid)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )


class UpdatedAtMixin:
    """Adds updated_at for rows whose state evolves after creation (docs/07)."""

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
