import uuid
from typing import TYPE_CHECKING, Any

import structlog

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
