"""API-layer dependencies: client IP, auth rate limiting, and domain services (docs/12 §2)."""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.service import ImageAnalysisService, get_analysis_service
from app.core.config import get_settings
from app.core.errors import RateLimitedError
from app.core.rate_limit import RateLimiter
from app.db.session import get_db
from app.services.scan_service import ScanService
from app.storage.local import LocalImageStore

_settings = get_settings()

# Single-process limiter for auth endpoints (docs/12 §2; Redis TODO — FUTURE PHASE).
auth_rate_limiter = RateLimiter(
    max_requests=_settings.AUTH_RATE_LIMIT_MAX,
    window_seconds=_settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
)

# Local media store (object storage is FUTURE — docs/15 §1).
image_store = LocalImageStore(_settings.MEDIA_DIR)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request) -> None:
    key = f"auth:{client_ip(request)}"
    if not auth_rate_limiter.check(key):
        raise RateLimitedError(
            details={"retry_after_seconds": _settings.AUTH_RATE_LIMIT_WINDOW_SECONDS}
        )


def get_image_store() -> LocalImageStore:
    return image_store


def get_scan_service(
    session: AsyncSession = Depends(get_db),
    analysis_service: ImageAnalysisService = Depends(get_analysis_service),
    store: LocalImageStore = Depends(get_image_store),
) -> ScanService:
    return ScanService(session, analysis_service=analysis_service, image_store=store)


def get_max_upload_bytes() -> int:
    return _settings.MAX_UPLOAD_BYTES
