"""Security primitives: Argon2id password hashing + JWT (docs/12 §1).

- Passwords: argon2-cffi PasswordHasher (Argon2id, memory-hard). Plaintext is never stored.
- Access tokens: JWT (PyJWT) with claims {sub, roles, type=access, iat, exp}.
- Refresh tokens: 256-bit random secrets; only their SHA-256 hash is persisted.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings
from app.core.errors import UnauthorizedError

_password_hasher = PasswordHasher()  # argon2id defaults


def hash_password(plain: str) -> str:
    return _password_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False
    except Exception:  # malformed hash or hashing failure — treat as verification failure
        return False


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict | None = None,
) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    payload: dict = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    # `expires_in` is a duration in seconds (OAuth2 semantics, docs/08 §1) — not a timestamp.
    return token, int(expires_delta.total_seconds())


def create_access_token(user_id: uuid.UUID, roles: list[str]) -> tuple[str, int]:
    settings = get_settings()
    return _create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(seconds=settings.access_token_expires_seconds),
        extra_claims={"roles": roles},
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(details={"reason": "invalid_token"}) from exc
    if payload.get("type") != "access":
        raise UnauthorizedError(details={"reason": "invalid_token"})
    return payload


def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, token_hash). Only the hash is stored (docs/07)."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
