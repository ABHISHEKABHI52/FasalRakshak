"""Farm request/response schemas (docs/08 §2)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=500)
    district: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    address: str | None = Field(default=None, max_length=500)
    district: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: str | None = None
    district: str | None = None
    state: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    field_count: int = 0