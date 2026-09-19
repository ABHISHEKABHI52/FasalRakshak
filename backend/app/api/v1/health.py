"""Liveness + readiness endpoints (docs/08 §10)."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import check_database_connection
from app.schemas.auth import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    return HealthResponse(status="ok", app=get_settings().APP_NAME)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe (database connectivity)",
    responses={503: {"description": "A component is unavailable"}},
)
async def ready() -> ReadinessResponse:
    db_ok = await check_database_connection()
    if not db_ok:
        # Handled by the exception layer? No — readiness returns 503 with component state.
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"db": False})  # type: ignore[return-value]
    return ReadinessResponse(db=True)
