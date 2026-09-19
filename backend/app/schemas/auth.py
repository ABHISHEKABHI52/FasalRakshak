"""Pydantic request/response schemas for Phase 1 (docs/08 §1, §11)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

PHONE_PATTERN = r"^\+?[0-9]{10,13}$"


# ---------- Requests ----------


class RegisterRequest(BaseModel):
    phone: str = Field(pattern=PHONE_PATTERN, examples=["+919876543210"])
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    preferred_language: str = Field(default="hi", pattern=r"^(en|hi|hinglish)$")
    district: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)
    consent_ml_use: bool = False

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name must not be blank")
        return v


class LoginRequest(BaseModel):
    phone_or_email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


# ---------- Responses ----------


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    email: str | None = None
    full_name: str
    preferred_language: str
    district: str | None = None
    state: str | None = None
    consent_ml_use: bool
    roles: list[str]
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RegisterResponse(BaseModel):
    user_id: uuid.UUID
    roles: list[str]


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str


class ReadinessResponse(BaseModel):
    db: bool
