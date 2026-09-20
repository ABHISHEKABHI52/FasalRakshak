"""FasalRakshak — application settings (docs/05 §2.2, docs/15 §2).

All configuration is environment-driven. Secrets are never hard-coded.
The SQLite dev default exists only so `uvicorn` can boot for local
smoke-testing without PostgreSQL; production MUST set a PostgreSQL URL.
"""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "FasalRakshak"
    ENV: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"

    # PostgreSQL in real deployments (docs/15): postgresql+asyncpg://user:pass@db:5432/fasalrakshak
    DATABASE_URL: str = "sqlite+aiosqlite:///./fasalrakshak_dev.db"

    # Dev placeholder ONLY. Guard below refuses it in production (docs/12 §4).
    # HS256 requires >= 32 bytes of key material (RFC 7518 §3.2).
    JWT_SECRET: str = Field(default="change-me-not-for-production-0123456789", min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    CORS_ORIGINS: str = "http://localhost:3000"

    # Basic auth rate limiting (docs/12 §2 — nginx enforces global limits in deployment)
    AUTH_RATE_LIMIT_MAX: int = 10
    AUTH_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ---- Media / image upload (Phase 2; docs/08 §3, docs/12 §3) ----
    MEDIA_DIR: str = "./media"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB upload cap (docs/08 §11)
    MAX_IMAGE_PIXELS: int = 24_000_000  # decompression-bomb guard (Pillow MAX_IMAGE_PIXELS)
    MIN_IMAGE_DIMENSION: int = 224  # prototype minimum usable side in px (docs/00 §16)
    STORED_IMAGE_MAX_DIMENSION: int = 1600  # downscale before storage
    STORED_IMAGE_JPEG_QUALITY: int = 85

    # ---- Image quality bands (PROTOTYPE thresholds — docs/00 §16, not validated) ----
    QUALITY_BAND_GOOD_MIN: int = 80
    QUALITY_BAND_ACCEPTABLE_MIN: int = 60
    QUALITY_BAND_POOR_MIN: int = 40

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def access_token_expires_seconds(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_expires_seconds(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    @model_validator(mode="after")
    def _validate_environment(self) -> "Settings":
        if self.JWT_SECRET == "change-me-not-for-production-0123456789" and self.ENV == "production":
            raise ValueError("JWT_SECRET must be replaced before running in production")
        if self.ENV not in {"development", "staging", "production"}:
            raise ValueError("ENV must be one of: development, staging, production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
