from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
import pytest

from src.dependencies.services import get_auth_service
from src.domain.exceptions.base import DomainError
from src.domain.exceptions.user import InvalidCredentialsError
from src.infrastructure.logging.middleware import exception_handler
from src.interfaces.api.v1.auth.main import router as auth_router


@pytest.fixture
def auth_use_cases() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def app(auth_use_cases: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.add_exception_handler(DomainError, exception_handler)
    app.include_router(auth_router, prefix="/api/v1")

    async def override_auth_service() -> AsyncMock:
        return auth_use_cases

    app.dependency_overrides[get_auth_service] = override_auth_service
    return app


def _make_user() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        username="john",
        email="john@example.com",
        is_admin=False,
    )


def _make_auth_result() -> SimpleNamespace:
    return SimpleNamespace(
        user=_make_user(),
        tokens=SimpleNamespace(access_token="access", refresh_token="refresh"),
    )


def test_register_returns_201(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    auth_use_cases.register.return_value = _make_user()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "john", "email": "john@example.com", "password": "secret123"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["user"]["username"] == "john"


def test_login_returns_401_for_invalid_credentials(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    auth_use_cases.login.side_effect = InvalidCredentialsError()

    response = client.post("/api/v1/auth/login", json={"identifier": "john", "password": "bad-pass"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_returns_401_for_invalid_refresh_token(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    auth_use_cases.refresh.side_effect = InvalidCredentialsError("Invalid refresh token.")

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "bad-token-value"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Invalid refresh token."


def test_refresh_returns_token_payload(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    auth_use_cases.refresh.return_value = _make_auth_result()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "valid-refresh-token-123"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"] == "access"


def test_logout_returns_204(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)

    response = client.post("/api/v1/auth/logout", json={"refresh_token": "valid-refresh-token"})

    assert response.status_code == status.HTTP_204_NO_CONTENT
    auth_use_cases.logout.assert_awaited_once()


def test_logout_returns_401_for_invalid_refresh_token(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    auth_use_cases.logout.side_effect = InvalidCredentialsError("Invalid refresh token.")

    response = client.post("/api/v1/auth/logout", json={"refresh_token": "bad-refresh-token"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["error"]["message"] == "Invalid refresh token."


def test_login_returns_token_payload(app: FastAPI, auth_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    auth_use_cases.login.return_value = _make_auth_result()

    response = client.post("/api/v1/auth/login", json={"identifier": "john", "password": "secret123"})

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["access_token"] == "access"
    assert payload["refresh_token"] == "refresh"
