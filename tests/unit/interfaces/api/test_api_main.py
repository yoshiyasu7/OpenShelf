from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI

from src.interfaces.api.main import create_api_app, lifespan


@pytest.mark.asyncio
async def test_lifespan_initializes_and_shutdowns_db(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace()
    db_manager = AsyncMock()
    monkeypatch.setattr("src.interfaces.api.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.interfaces.api.main.init_db_manager", lambda _settings: db_manager)

    async with lifespan(FastAPI()):
        pass

    db_manager.initialize.assert_awaited_once()
    db_manager.shutdown.assert_awaited_once()


def test_create_api_app_builds_application(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = SimpleNamespace(api=SimpleNamespace(title="OpenShelf", version="1.0.0", debug=False))
    monkeypatch.setattr("src.interfaces.api.main.get_settings", lambda: settings)
    monkeypatch.setattr("src.interfaces.api.main.configure_logging", lambda: None)

    app = create_api_app()

    assert isinstance(app, FastAPI)
    assert app.title == "OpenShelf"
    assert any(route.path == "/health" for route in app.routes)
    assert any(route.path == "/api/v1/auth/login" for route in app.routes)
