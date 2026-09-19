"""Roles and user-role assignment (docs/07 §1)."""

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RoleName(str, enum.Enum):
    FARMER = "FARMER"
    EXTENSION_WORKER = "EXTENSION_WORKER"
    EXPERT = "EXPERT"
    OFFICER = "OFFICER"
    ADMIN = "ADMIN"


ROLE_DESCRIPTIONS: dict[str, str] = {
    RoleName.FARMER.value: "Owns farms, fields, scans and advisories",
    RoleName.EXTENSION_WORKER.value: "Assists farmers in the field",
    RoleName.EXPERT.value: "Validates and corrects AI diagnoses",
    RoleName.OFFICER.value: "District-level surveillance and response",
    RoleName.ADMIN.value: "System administration (audited)",
}


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        SAEnum(
            RoleName,
            name="role_name",
            values_callable=lambda e: [m.value for m in e],
            native_enum=False,  # VARCHAR + CHECK: portable across PostgreSQL/SQLite
        ),
        unique=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    users: Mapped[list["UserRole"]] = relationship(back_populates="role")


class UserRole(Base):
    """M:N users<->roles via user_roles (docs/07 §1)."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True
    )

    user: Mapped["User"] = relationship(back_populates="role_links")  # type: ignore[name-defined]
    role: Mapped[Role] = relationship(back_populates="users")
