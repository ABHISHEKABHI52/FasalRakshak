"""Request-context middleware: request ID + structured access logging (docs/12 §5)."""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("fasalrakshak.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assigns a request ID, logs method/path/status/duration, echoes X-Request-ID."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            status_code = getattr(locals().get("response"), "status_code", 500)
            logger.info(
                "request method=%s path=%s status=%s duration_ms=%s request_id=%s",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                request_id,
            )
        response.headers["X-Request-ID"] = request_id
        return response
