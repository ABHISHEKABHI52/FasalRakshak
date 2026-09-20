"""farmer core loop: farms, fields, crops, crop_cycles, images, crop_scans,
image_quality_results, diagnoses

Revision ID: 0002
Revises: 0001
Create Date: Phase 2 (docs/07 §2–4)

Also seeds the documented MVP crop catalogue (docs/00 §27.1: tomato, potato,
cotton) with PROTOTYPE stage thresholds — not agronomically validated.
"""

import uuid as _uuid  # noqa: E402  (used inside upgrade)
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_JSON = JSONB().with_variant(sa.JSON(), "sqlite")

CROP_STAGE_VALUES = ("seedling", "vegetative", "flowering", "fruiting", "maturity")
CYCLE_STATUS_VALUES = ("active", "completed", "abandoned")
PLANT_PART_VALUES = ("leaf", "stem", "fruit", "whole_plant", "trap")
SCAN_STATUS_VALUES = (
    "pending_image", "quality_checking", "quality_rejected",
    "analyzing", "completed", "failed",
)
QUALITY_CATEGORY_VALUES = ("good", "acceptable", "poor", "unusable")
DIAGNOSIS_STATUS_VALUES = (
    "diagnosed", "insufficient_evidence", "referred_expert",
    "expert_confirmed", "expert_corrected", "rejected",
)

# Documented MVP catalogue — single source of truth shared with the test fixtures.
from app.db.seed_data import CROP_SEED as CROP_ROWS


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    _location_type = (
        Geography(geometry_type="POINT", srid=4326) if _is_postgres() else sa.Text()
    )

    op.create_table(
        "crops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name_en", sa.String(length=80), nullable=False),
        sa.Column("name_hi", sa.String(length=80), nullable=False),
        sa.Column("scientific_name", sa.String(length=120), nullable=True),
        sa.Column("stage_model", _JSON, nullable=True),
        sa.Column("is_supported", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_crops")),
        sa.UniqueConstraint("code", name=op.f("uq_crops_code")),
    )

    op.create_table(
        "farms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("district", sa.String(length=80), nullable=True),
        sa.Column("state", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], name=op.f("fk_farms_owner_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farms")),
    )
    op.create_index(op.f("ix_farms_owner_active"), "farms", ["owner_id", "is_active"], unique=False)

    op.create_table(
        "fields",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("farm_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("area_hectares", sa.Numeric(6, 2), nullable=True),
        sa.Column("location", _location_type, nullable=True),
        sa.Column("soil_type", sa.String(length=40), nullable=True),
        sa.Column("district_code", sa.String(length=10), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farms.id"], name=op.f("fk_fields_farm_id_farms"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_fields")),
    )
    op.create_index(op.f("ix_fields_farm_active"), "fields", ["farm_id", "is_active"], unique=False)
    if _is_postgres():
        op.create_index(
            "ix_fields_location_gist", "fields", ["location"], unique=False, postgresql_using="gist"
        )

    # Seed the documented MVP catalogue (deterministic UUIDs → stable references).
    from app.db.base import utcnow as _utcnow

    op.bulk_insert(
        sa.table(
            "crops",
            sa.column("id", sa.Uuid),
            sa.column("code", sa.String),
            sa.column("name_en", sa.String),
            sa.column("name_hi", sa.String),
            sa.column("scientific_name", sa.String),
            sa.column("stage_model", _JSON),
            sa.column("is_supported", sa.Boolean),
            sa.column("created_at", sa.DateTime),
        ),
        [
            {
                **row,
                "id": _uuid.uuid5(_uuid.NAMESPACE_URL, f"crop:{row['code']}"),
                "created_at": _utcnow(),
            }
            for row in CROP_ROWS
        ],
    )

    op.create_table(
        "crop_cycles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False),
        sa.Column("crop_id", sa.Uuid(), nullable=False),
        sa.Column("variety", sa.String(length=80), nullable=True),
        sa.Column("sowing_date", sa.Date(), nullable=False),
        sa.Column("expected_harvest_date", sa.Date(), nullable=True),
        sa.Column(
            "current_stage", sa.Enum(*CROP_STAGE_VALUES, name="crop_stage", native_enum=False),
            nullable=False,
        ),
        sa.Column("stage_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(*CYCLE_STATUS_VALUES, name="cycle_status", native_enum=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crop_id"], ["crops.id"], name=op.f("fk_crop_cycles_crop_id_crops"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["field_id"], ["fields.id"], name=op.f("fk_crop_cycles_field_id_fields"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_crop_cycles")),
        sa.CheckConstraint(
            "expected_harvest_date IS NULL OR expected_harvest_date > sowing_date",
            name=op.f("ck_crop_cycles_harvest_after_sowing"),
        ),
    )
    op.create_index(
        op.f("ix_crop_cycles_field_sowing"), "crop_cycles", ["field_id", "sowing_date"], unique=False
    )

    op.create_table(
        "images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_images")),
        sa.CheckConstraint("size_bytes > 0", name=op.f("ck_images_size_positive")),
        sa.UniqueConstraint("checksum_sha256", name=op.f("uq_images_checksum_sha256")),
    )

    op.create_table(
        "crop_scans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("client_scan_uuid", sa.Uuid(), nullable=False),
        sa.Column("field_id", sa.Uuid(), nullable=False),
        sa.Column("crop_cycle_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "plant_part", sa.Enum(*PLANT_PART_VALUES, name="plant_part", native_enum=False),
            nullable=False,
        ),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(*SCAN_STATUS_VALUES, name="scan_status", native_enum=False),
            server_default="pending_image",
            nullable=False,
        ),
        sa.Column("status_reason", sa.String(length=60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["crop_cycle_id"], ["crop_cycles.id"], name=op.f("fk_crop_scans_crop_cycle_id_crop_cycles"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["field_id"], ["fields.id"], name=op.f("fk_crop_scans_field_id_fields"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["image_id"], ["images.id"], name=op.f("fk_crop_scans_image_id_images"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_crop_scans_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_crop_scans")),
        sa.UniqueConstraint("client_scan_uuid", name=op.f("uq_crop_scans_client_scan_uuid")),
    )
    op.create_index(
        op.f("ix_crop_scans_field_created"), "crop_scans", ["field_id", "created_at"], unique=False
    )
    op.create_index(op.f("ix_crop_scans_status"), "crop_scans", ["status"], unique=False)

    op.create_table(
        "image_quality_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column("image_id", sa.Uuid(), nullable=False),
        sa.Column("quality_score", sa.SmallInteger(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(*QUALITY_CATEGORY_VALUES, name="quality_category", native_enum=False),
            nullable=False,
        ),
        sa.Column("reasons", _JSON, nullable=True),
        sa.Column("leaf_coverage", sa.Float(), nullable=True),
        sa.Column("usable", sa.Boolean(), nullable=False),
        sa.Column("model_ref", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["image_id"], ["images.id"], name=op.f("fk_image_quality_results_image_id_images"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["scan_id"], ["crop_scans.id"], name=op.f("fk_image_quality_results_scan_id_crop_scans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_image_quality_results")),
        sa.CheckConstraint("quality_score BETWEEN 0 AND 100", name=op.f("ck_image_quality_results_score_range")),
        sa.UniqueConstraint("scan_id", name=op.f("uq_image_quality_results_scan_id")),
    )

    op.create_table(
        "diagnoses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scan_id", sa.Uuid(), nullable=False),
        sa.Column(
            "final_status",
            sa.Enum(*DIAGNOSIS_STATUS_VALUES, name="diagnosis_status", native_enum=False),
            nullable=False,
        ),
        sa.Column("primary_label_code", sa.String(length=60), nullable=True),
        sa.Column("fused_confidence", sa.Float(), nullable=True),
        sa.Column("differential", _JSON, nullable=True),
        sa.Column("evidence_trace", _JSON, nullable=True),
        sa.Column("final_label_code", sa.String(length=60), nullable=True),
        sa.Column("analysis_model", sa.String(length=60), nullable=True),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["scan_id"], ["crop_scans.id"], name=op.f("fk_diagnoses_scan_id_crop_scans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_diagnoses")),
        sa.UniqueConstraint("scan_id", name=op.f("uq_diagnoses_scan_id")),
    )


def downgrade() -> None:
    op.drop_table("diagnoses")
    op.drop_table("image_quality_results")
    op.drop_index(op.f("ix_crop_scans_status"), table_name="crop_scans")
    op.drop_index(op.f("ix_crop_scans_field_created"), table_name="crop_scans")
    op.drop_table("crop_scans")
    op.drop_table("images")
    op.drop_index(op.f("ix_crop_cycles_field_sowing"), table_name="crop_cycles")
    op.drop_table("crop_cycles")
    if _is_postgres():
        op.drop_index("ix_fields_location_gist", table_name="fields")
    op.drop_index(op.f("ix_fields_farm_active"), table_name="fields")
    op.drop_table("fields")
    op.drop_index(op.f("ix_farms_owner_active"), table_name="farms")
    op.drop_table("farms")
    op.drop_table("crops")
