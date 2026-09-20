"""Stable application error types + RFC7807-style error envelope (docs/08 §11).

Every client-visible error is: {"code", "message_key", "details"}.
Stack traces are never sent to clients (docs/12 §7).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("fasalrakshak.errors")


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    message_key = "errors.internal_error"

    def __init__(
        self,
        message_key: str | None = None,
        details: dict | list | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.message_key = message_key or self.message_key
        self.details = details
        self.code = code or self.code
        self.status_code = status_code or self.status_code
        super().__init__(self.code)


class BadRequestError(AppError):
    status_code, code, message_key = 400, "bad_request", "errors.bad_request"


class UnauthorizedError(AppError):
    status_code, code, message_key = 401, "unauthorized", "errors.unauthorized"


class ForbiddenError(AppError):
    status_code, code, message_key = 403, "forbidden", "errors.forbidden"


class NotFoundError(AppError):
    status_code, code, message_key = 404, "not_found", "errors.not_found"


class ConflictError(AppError):
    status_code, code, message_key = 409, "conflict", "errors.conflict"


class PayloadTooLargeError(AppError):
    """413 — upload exceeds the configured size cap (docs/08 §11)."""

    status_code, code, message_key = 413, "payload_too_large", "errors.payload_too_large"


class UnsupportedMediaError(AppError):
    """415 — not a supported image format (docs/08 §11)."""

    status_code, code, message_key = 415, "unsupported_media", "errors.unsupported_media"


class QualityUnusableError(AppError):
    """422 — image failed the quality gate; no diagnosis is produced (docs/08 §11, AC-01)."""

    status_code, code, message_key = 422, "quality_unusable", "errors.quality_unusable"


class UnprocessableError(AppError):
    status_code, code, message_key = 422, "unprocessable", "errors.unprocessable"


class RateLimitedError(AppError):
    status_code, code, message_key = 429, "rate_limited", "errors.rate_limited"


class ServiceUnavailableError(AppError):
    status_code, code, message_key = 503, "service_unavailable", "errors.service_unavailable"


def _error_payload(code: str, message_key: str, details: dict | list | None) -> dict:
    return {"code": code, "message_key": message_key, "details": details or {}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def on_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = []
        for err in exc.errors():
            loc = ".".join(str(p) for p in err.get("loc", []) if p != "body")
            fields.append({"field": loc, "message": err.get("msg", "invalid")})
        return JSONResponse(
            status_code=400,
            content=_error_payload("validation_error", "errors.validation_error", {"fields": fields}),
        )

    @app.exception_handler(AppError)
    async def on_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message_key, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def on_http_exception(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            code, key = "not_found", "errors.not_found"
        elif exc.status_code == 401:
            code, key = "unauthorized", "errors.unauthorized"
        elif exc.status_code == 405:
            code, key = "method_not_allowed", "errors.method_not_allowed"
        else:
            code, key = f"http_{exc.status_code}", f"errors.http_{exc.status_code}"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(code, key, None),
        )

    @app.exception_handler(Exception)
    async def on_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_error_payload("internal_error", "errors.internal_error", None),
        )
