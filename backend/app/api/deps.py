"""API-layer dependencies: client IP extraction + auth rate limiting (docs/12 §2)."""

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import RateLimitedError
from app.core.rate_limit import RateLimiter

_settings = get_settings()

# Single-process limiter for auth endpoints (docs/12 §2; Redis TODO — FUTURE PHASE).
auth_rate_limiter = RateLimiter(
    max_requests=_settings.AUTH_RATE_LIMIT_MAX,
    window_seconds=_settings.AUTH_RATE_LIMIT_WINDOW_SECONDS,
)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce_auth_rate_limit(request: Request) -> None:
    key = f"auth:{client_ip(request)}"
    if not auth_rate_limiter.check(key):
        raise RateLimitedError(
            details={"retry_after_seconds": _settings.AUTH_RATE_LIMIT_WINDOW_SECONDS}
        )
