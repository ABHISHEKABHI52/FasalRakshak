"""Crop catalogue schemas (docs/08 §2 — GET /crops is read-only for farmers)."""

import uuid

from pydantic import BaseModel, ConfigDict


class CropResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name_en: str
    name_hi: str
    scientific_name: str | None = None
    is_supported: bool
    stage_model: dict | None = None