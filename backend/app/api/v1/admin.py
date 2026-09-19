"""Admin endpoints (RBAC demonstration — full admin console TODO — FUTURE PHASE)."""

from fastapi import APIRouter, Depends

from app.auth.deps import require_role
from app.core.config import get_settings
from app.models.role import RoleName
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping", summary="RBAC check: ADMIN-only")
async def ping(_: User = Depends(require_role(RoleName.ADMIN))) -> dict[str, str]:
    return {"status": "ok", "app": get_settings().APP_NAME}
