"""FasalRakshak API — application factory (docs/05 §2).

Phase 1 scope: auth foundation, RBAC, health/readiness, audit logging.
Not implemented yet (TODO — FUTURE PHASE): scans, AI pipeline, risk engine,
GIS, RAG, weather, expert/officer workflows. See docs/IMPLEMENTATION_STATUS.md.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title="FasalRakshak API",
        version="0.1.0",
        summary="AI-Powered Crop Health & Early Warning Platform (SIH26131)",
        docs_url=None if settings.ENV == "production" else "/api/docs",
        redoc_url=None,
        openapi_url=None if settings.ENV == "production" else "/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)

    register_error_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
