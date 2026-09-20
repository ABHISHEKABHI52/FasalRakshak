"""Scan / image / quality / analysis schemas (docs/08 §3–§5).

`analysis.status` mirrors diagnoses.final_status: INSUFFICIENT_EVIDENCE is a
successful outcome, not an error (docs/06 §9). `is_mock` marks stub inference so a
test double can never be mistaken for a real prediction.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.scan import PlantPart, QualityCategory, ScanStatus


class ScanCreate(BaseModel):
    field_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    plant_part: PlantPart
    captured_at: datetime
    client_scan_uuid: uuid.UUID = Field(
        description="Client-generated idempotency key — resubmitting it returns the original scan"
    )


class ScanCreatedResponse(BaseModel):
    scan_id: uuid.UUID
    status: ScanStatus


class ImageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mime_type: str
    size_bytes: int
    width: int
    height: int


class QualitySummary(BaseModel):
    quality_score: int
    category: QualityCategory
    usable: bool
    leaf_coverage: float | None = None
    reasons: list[dict] = Field(default_factory=list)
    metrics: dict | None = None
    model_ref: str | None = None


class AnalysisSummary(BaseModel):
    status: str
    primary_label_code: str | None = None
    confidence: float | None = None
    candidates: list[dict] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    model_name: str | None = None
    model_version: str | None = None
    is_mock: bool = False
    note: str | None = None


class ScanResponse(BaseModel):
    id: uuid.UUID
    client_scan_uuid: uuid.UUID
    field_id: uuid.UUID
    crop_cycle_id: uuid.UUID
    plant_part: PlantPart
    captured_at: datetime
    status: ScanStatus
    status_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    image: ImageSummary | None = None
    quality: QualitySummary | None = None
    analysis: AnalysisSummary | None = None


class ImageUploadResponse(BaseModel):
    scan_id: uuid.UUID
    image_id: uuid.UUID
    status: ScanStatus
    quality: QualitySummary
    analysis: AnalysisSummary | None = None


class ScanListResponse(BaseModel):
    items: list[ScanResponse]
    next_cursor: str | None = None