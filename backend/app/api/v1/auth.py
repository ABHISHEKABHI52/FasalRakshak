"""Authentication endpoints (docs/08 Â§1).

POST /register  â€” create FARMER account (rate-limited)
POST /login     â€” issue access token + refresh cookie (rate-limited)
POST /refresh   â€” rotate refresh cookie, issue new access token
POST /logout    â€” revoke refresh token, clear cookie
GET  /me        â€” authenticated profile
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import client_ip, enforce_auth_rate_limit
from app.auth.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import create_access_token, generate_refresh_token, hash_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    UserResponse,
)
from app.services.audit_service import AuditService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "fr_refresh"

_settings = get_settings()


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_token,
        max_age=int(_settings.refresh_token_expires_seconds),
        httponly=True,
        secure=_settings.ENV != "development",
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=RegisterResponse)
async def register(
    data: RegisterRequest,
    request: Request,
    _: None = Depends(enforce_auth_rate_limit),
    session: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    service = UserService(session)
    user = await service.register(data)
    await AuditService(session).record(
        action="user.register",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_hash=hash_token(client_ip(request)),
        after={"roles": ["FARMER"]},
    )
    await session.commit()
    # Re-fetch with roles eagerly loaded (relationship IO is unsafe post-commit).
    user = await service.repo.get_by_id(user.id)
    assert user is not None  # just created within this transaction
    return RegisterResponse(user_id=user.id, roles=user.roles)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    _: None = Depends(enforce_auth_rate_limit),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = UserService(session)
    audit = AuditService(session)
    ip_hash = hash_token(client_ip(request))
    now = datetime.now(timezone.utc)
    try:
        user = await service.authenticate(data.phone_or_email, data.password)
    except UnauthorizedError:
        await audit.record(action="user.login_failed", resource_type="user", ip_hash=ip_hash)
        await session.commit()
        raise
    user.last_login_at = now
    raw_refresh, refresh_hash = generate_refresh_token()
    await RefreshTokenRepository(session).create(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=now + timedelta(seconds=_settings.refresh_token_expires_seconds),
    )
    await audit.record(
        action="user.login",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        ip_hash=ip_hash,
    )
    await session.commit()
    access_token, expires_in = create_access_token(user.id, user.roles)
    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotate the refresh token and issue a new access token (docs/12 Â§1)."""
    if not refresh_cookie:
        raise UnauthorizedError(details={"reason": "missing_refresh_token"})
    repo = RefreshTokenRepository(session)
    now = datetime.now(timezone.utc)
    token = await repo.find_active_by_hash(hash_token(refresh_cookie), now)
    if token is None:
        raise UnauthorizedError(details={"reason": "invalid_refresh_token"})
    user = await UserService(session).repo.get_by_id(token.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError(details={"reason": "invalid_user"})
    await repo.revoke(token, now)
    raw_new, new_hash = generate_refresh_token()
    await repo.create(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=now + timedelta(seconds=_settings.refresh_token_expires_seconds),
    )
    await session.commit()
    access_token, expires_in = create_access_token(user.id, user.roles)
    _set_refresh_cookie(response, raw_new)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    refresh_cookie: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    session: AsyncSession = Depends(get_db),
) -> Response:
    if refresh_cookie:
        repo = RefreshTokenRepository(session)
        token = await repo.find_active_by_hash(hash_token(refresh_cookie), datetime.now(timezone.utc))
        if token is not None:
            await repo.revoke(token, datetime.now(timezone.utc))
            await session.commit()
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
