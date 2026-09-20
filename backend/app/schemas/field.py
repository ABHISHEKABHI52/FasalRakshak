"""Field request/response schemas (docs/08 §2). Location is {lat, lng} (docs/07 §9)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.geo import parse_point_wkt


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90, description="Latitude (WGS84)")
    lng: float = Field(ge=-180, le=180, description="Longitude (WGS84)")


class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    name: str
    area_hectares: float | None = None
    location: GeoPoint | None = None
    soil_type: str | None = None
    district_code: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    crop_cycle_count: int = 0

    @field_validator("location", mode="before")
    @classmethod
    def _accept_stored_wkt(cls, value: object) -> object:
        """ORM rows carry WKT/EWKT; convert to {lat, lng} for the API contract."""
        if isinstance(value, str):
            parsed = parse_point_wkt(value)
            return {"lat": parsed[0], "lng": parsed[1]} if parsed else None
        return value


class FieldCreate(BaseModel):
    farm_id: uuid.UUID
    name: str = Field(min_length=1, max_length=120)
    area_hectares: float | None = Field(default=None, gt=0, le=10_000)
    location: GeoPoint | None = None
    soil_type: str | None = Field(default=None, max_length=40)
    district_code: str | None = Field(default=None, max_length=10)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be blank")
        return value


class FieldUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    area_hectares: float | None = Field(default=None, gt=0, le=10_000)
    location: GeoPoint | None = None
    soil_type: str | None = Field(default=None, max_length=40)
    district_code: str | None = Field(default=None, max_length=10)