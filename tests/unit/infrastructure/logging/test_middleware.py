from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError

from src.domain.exceptions.base import DomainError
from src.infrastructure.logging import middleware


def test_resolve_endpoint_name_handles_missing_and_present() -> None:
    assert middleware._resolve_endpoint_name({"endpoint": None}) is None

    def handler() -> None:
        return None

    assert middleware._resolve_endpoint_name({"endpoint": handler}) == "handler"


@pytest.mark.asyncio
async def test_request_context_middleware_passthrough_for_non_http() -> None:
    app = AsyncMock()
    mw = middleware.RequestContextMiddleware(app=app)

    await mw({"type": "websocket"}, AsyncMock(), AsyncMock())

    app.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_context_middleware_adds_request_id_and_logs_info(monkeypatch: pytest.MonkeyPatch) -> None:
    sent_messages: list[dict] = []

    async def app(scope, _receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    mw = middleware.RequestContextMiddleware(app=app)
    info_log = Mock()
    error_log = Mock()
    monkeypatch.setattr(middleware.request_log, "info", info_log)
    monkeypatch.setattr(middleware.request_log, "error", error_log)

    async def send(message):
        sent_messages.append(message)

    scope = {"type": "http", "path": "/health", "method": "GET", "headers": []}
    await mw(scope, AsyncMock(), send)

    assert any(h[0] == middleware.REQUEST_ID_HEADER for h in sent_messages[0]["headers"])
    info_log.assert_called_once()
    error_log.assert_not_called()


@pytest.mark.asyncio
async def test_request_context_middleware_logs_error_for_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    async def app(_scope, _receive, send):
        await send({"type": "http.response.start", "status": 500, "headers": []})

    mw = middleware.RequestContextMiddleware(app=app)
    info_log = Mock()
    error_log = Mock()
    monkeypatch.setattr(middleware.request_log, "info", info_log)
    monkeypatch.setattr(middleware.request_log, "error", error_log)

    await mw({"type": "http", "path": "/x", "method": "GET", "headers": []}, AsyncMock(), AsyncMock())

    error_log.assert_called_once()
    info_log.assert_not_called()


@pytest.mark.asyncio
async def test_exception_handler_domain_error(monkeypatch: pytest.MonkeyPatch) -> None:
    warning_log = Mock()
    monkeypatch.setattr(middleware.error_log, "warning", warning_log)
    request = Request(scope={"type": "http", "method": "GET", "path": "/", "headers": []})
    exc = DomainError(message="boom", error_code="ERR", status_code=418)

    response = await middleware.exception_handler(request, exc)

    assert response.status_code == 418
    warning_log.assert_called_once()


@pytest.mark.asyncio
async def test_exception_handler_validation_error() -> None:
    request = Request(scope={"type": "http", "method": "POST", "path": "/", "headers": []})
    exc = RequestValidationError([{"loc": ("body", "field"), "msg": "missing", "type": "value_error.missing"}])

    response = await middleware.exception_handler(request, exc)

    assert response.status_code == 422
    assert b"VALIDATION_ERROR" in response.body


@pytest.mark.asyncio
async def test_exception_handler_unhandled_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    error_log = Mock()
    monkeypatch.setattr(middleware.error_log, "error", error_log)
    request = Request(scope={"type": "http", "method": "GET", "path": "/", "headers": []})

    response = await middleware.exception_handler(request, RuntimeError("boom"))

    assert response.status_code == 500
    error_log.assert_called_once()
