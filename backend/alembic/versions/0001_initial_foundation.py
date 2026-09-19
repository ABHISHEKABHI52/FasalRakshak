"""initial foundation: roles, users, user_roles, refresh_tokens, audit_logs

Revision ID: 0001
Revises:
Create Date: Phase 1 — FasalRakshak foundation (docs/07 §1, §7)

Seeds the five system roles with fixed IDs so later migrations and
application code can reference them deterministically.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_JSON = JSONB().with_variant(sa.JSON(), "sqlite")
_BIGINT = sa.BigInteger().with_variant(sa.Integer(), "sqlite")

ROLE_ROWS = [
    {"id": 1, "name": "FARMER", "description": "Owns farms, fields, scans and advisories"},
    {"id": 2, "name": "EXTENSION_WORKER", "description": "Assists farmers in the field"},
    {"id": 3, "name": "EXPERT", "description": "Validates and corrects AI diagnoses"},
    {"id": 4, "name": "OFFICER", "description": "District-level surveillance and response"},
    {"id": 5, "name": "ADMIN", "description": "System administration (audited)"},
]


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.Enum(
                "FARMER", "EXTENSION_WORKER", "EXPERT", "OFFICER", "ADMIN",
                name="role_name",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("preferred_language", sa.String(length=8), nullable=False),
        sa.Column("district", sa.String(length=80), nullable=True),
        sa.Column("state", sa.String(length=80), nullable=True),
        sa.Column("consent_ml_use", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("phone", name=op.f("uq_users_phone")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_user_roles_role_id_roles"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_roles")),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_refresh_tokens_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_refresh_tokens_token_hash")),
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_expires"), "refresh_tokens", ["user_id", "expires_at"], unique=False
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", _BIGINT, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=40), nullable=False),
        sa.Column("resource_type", sa.String(length=30), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("before", _JSON, nullable=True),
        sa.Column("after", _JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_audit_logs_user_id_users"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(
        op.f("ix_audit_logs_resource"), "audit_logs", ["resource_type", "resource_id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_logs_user_created"), "audit_logs", ["user_id", "created_at"], unique=False
    )

    # Seed the five system roles (deterministic IDs).
    roles_target = sa.table(
        "roles",
        sa.column("id", sa.SmallInteger),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(roles_target, [dict(r) for r in ROLE_ROWS])


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_user_created"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_refresh_tokens_user_expires"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")

