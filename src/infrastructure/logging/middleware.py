import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import structlog

from .config import get_logger

log = get_logger(__name__)

# HTTP header name used to propagate request ID between services.
REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Bind per-request context (request_id, user_id, path, method) into structlog.contextvars.
    """
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())

        raw_user = getattr(request.state, "user", None)
        user_id = None
        if raw_user is not None:
            user_id = getattr(raw_user, "id", None)

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            user_id=user_id,
            path=request.url.path,
            method=request.method,
        )

        try:
            response = await call_next(request)

            # Ensure the request ID is visible to the caller.
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()

