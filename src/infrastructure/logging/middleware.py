import uuid
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.domain.exceptions.base import DomainError

from .config import get_logger

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

log = get_logger(__name__)

REQUEST_ID_HEADER = b"x-request-id"


class RequestContextMiddleware:
    """
    Pure ASGI Middleware for managing request context and logging.
    """

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

        state: dict[str, Any] = scope.get("state", {})
        user = state.get("user")
        user_id = getattr(user, "id", None) if user else None

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=user_id,
            path=path,
            method=method,
        )

        async def send_wrapper(message: Message) -> None:
            """Intercept the response start to add the X-Request-ID header."""
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.append((REQUEST_ID_HEADER, request_id.encode("utf-8")))
                message["headers"] = response_headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            structlog.contextvars.clear_contextvars()


async def exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """
    A single place to handle all application errors.
    """
    # Catches all errors inherited from DomainError
    if isinstance(exc, DomainError):
        log.warning(
            "domain_error",
            error_code=exc.error_code,
            status_code=exc.status_code,
            message=exc.message
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

    # Catches all pydantic errors
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": exc.errors()
                }
            }
        )

    # Catches all unexpected errors (500)
    log.error(
        "unhandled_exception",
        exception=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
