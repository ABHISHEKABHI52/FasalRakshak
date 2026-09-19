"""Authentication + RBAC dependencies (docs/12 §1, docs/03 §2).

Usage in routers:
    user: User = Depends(require_role(RoleName.ADMIN))
"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.role import RoleName
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token (Bearer)")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError(details={"reason": "missing_token"})
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(str(payload.get("sub")))
    except ValueError as exc:
        raise UnauthorizedError(details={"reason": "invalid_token"}) from exc
    user = await UserRepository(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError(details={"reason": "invalid_user"})
    return user


def require_role(*allowed: RoleName):
    """Dependency factory enforcing RBAC (docs/03 §2 matrix)."""

    allowed_values = {role.value for role in allowed}

    async def dependency(user: User = Depends(get_current_user)) -> User:
        user_roles = set(user.roles)
        if not user_roles & allowed_values:
            raise ForbiddenError(details={"required_roles": sorted(allowed_values)})
        return user

    return dependency
