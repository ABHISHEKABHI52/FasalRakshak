"""Crop-cycle request/response schemas (docs/08 §2).

`current_stage` is DERIVED server-side from the sowing date using the crop's
prototype `stage_model` (docs/07 §2) — clients never set it directly.
"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.crop import CropStage, CycleStatus


class CropCycleCreate(BaseModel):
    field_id: uuid.UUID
    crop_id: uuid.UUID
    variety: str | None = Field(default=None, max_length=80)
    sowing_date: date
    expected_harvest_date: date | None = None

    @model_validator(mode="after")
    def _check_dates(self) -> "CropCycleCreate":
        if self.sowing_date > date.today():
            raise ValueError("sowing_date cannot be in the future")
        if self.expected_harvest_date and self.expected_harvest_date <= self.sowing_date:
            raise ValueError("expected_harvest_date must be after sowing_date")
        return self


class CropCycleUpdate(BaseModel):
    variety: str | None = Field(default=None, max_length=80)
    expected_harvest_date: date | None = None
    status: CycleStatus | None = None


class CropCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_id: uuid.UUID
    crop_id: uuid.UUID
    crop_code: str
    crop_name_en: str
    crop_name_hi: str
    variety: str | None = None
    sowing_date: date
    expected_harvest_date: date | None = None
    current_stage: CropStage
    stage_updated_at: datetime | None = None
    status: CycleStatus
    created_at: datetime
    updated_at: datetime