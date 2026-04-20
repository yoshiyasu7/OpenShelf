import time
import uuid
from typing import TYPE_CHECKING

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import DomainError

from .config import get_logger

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Logger names under "openshelf.api" so records land in api.log via the
# api_logger hierarchy configured in config.configure_logging.
request_log = get_logger("openshelf.api.http")
error_log = get_logger("openshelf.api.errors")

REQUEST_ID_HEADER = b"x-request-id"


def _resolve_endpoint_name(scope: Scope) -> str | None:
    """Return the FastAPI handler function name, if routing has happened."""
    endpoint = scope.get("endpoint")
    if endpoint is None:
        return None
    name = getattr(endpoint, "__name__", None)
    return name if isinstance(name, str) else None


class RequestContextMiddleware:
    """ASGI middleware: binds per-request context and emits request_completed."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id_bytes = headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()).encode())
        request_id = request_id_bytes.decode("utf-8")

        path = scope.get("path", "")
        method = scope.get("method", "")

        # user_id is bound later by the auth dependency — see
        # src/dependencies/auth.py. Anonymous requests never get the field.
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            path=path,
            method=method,
        )

        status_code = 0
        started_at = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = int(message.get("status", 0))
                response_headers = list(message.get("headers", []))
                response_headers.append((REQUEST_ID_HEADER, request_id.encode("utf-8")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
            endpoint_name = _resolve_endpoint_name(scope)

            # 4xx are client-side issues; only 5xx counts as a server error.
            if status_code >= 500:
                request_log.error(
                    "request_completed",
                    status=status_code,
                    duration_ms=duration_ms,
                    endpoint=endpoint_name,
                )
            else:
                request_log.info(
                    "request_completed",
                    status=status_code,
                    duration_ms=duration_ms,
                    endpoint=endpoint_name,
                )
            structlog.contextvars.clear_contextvars()


async def exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Single entry point that converts any exception into a JSON response."""
    if isinstance(exc, DomainError):
        error_log.warning(
            "domain_error",
            error_code=exc.error_code,
            status_code=exc.status_code,
            message=exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                }
            },
        )

    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": exc.errors(),
                }
            },
        )

    error_log.error("unhandled_exception", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
