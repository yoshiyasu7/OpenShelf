from unittest.mock import AsyncMock

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.interfaces.api.health.main import router as health_router


def test_health_returns_app_and_db_state(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(health_router)
    db_manager = AsyncMock()
    db_manager.health_check.return_value = {
        "status": "up",
        "available": True,
        "pool_size": 5,
        "checked_in": 5,
        "checked_out": 0,
        "overflow": 0,
        "invalid": 0,
    }
    monkeypatch.setattr("src.interfaces.api.health.main.get_db_manager", lambda: db_manager)
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["status"] == "up"
    assert payload["app"]["status"] == "up"
    assert "uptime_seconds" in payload["app"]
    assert payload["db"]["available"] is True


def test_db_health_returns_database_state(monkeypatch) -> None:
    app = FastAPI()
    app.include_router(health_router)
    db_manager = AsyncMock()
    db_manager.health_check.return_value = {"status": "degraded", "available": False}
    monkeypatch.setattr("src.interfaces.api.health.main.get_db_manager", lambda: db_manager)
    client = TestClient(app)

    response = client.get("/health/db")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "degraded", "available": False}
