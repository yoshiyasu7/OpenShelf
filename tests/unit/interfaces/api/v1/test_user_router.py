from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
import pytest

from src.dependencies.auth import get_current_admin, get_current_user
from src.dependencies.services import get_user_service
from src.interfaces.api.v1.user.main import router as user_router


def _make_user(*, is_admin: bool) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        username="john",
        email="john@example.com",
        is_admin=is_admin,
    )


@pytest.fixture
def user_use_cases() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def app(user_use_cases: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(user_router, prefix="/api/v1")

    async def override_user_service() -> AsyncMock:
        return user_use_cases

    async def override_current_user() -> SimpleNamespace:
        return _make_user(is_admin=False)

    async def override_current_admin() -> SimpleNamespace:
        return _make_user(is_admin=True)

    app.dependency_overrides[get_user_service] = override_user_service
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_admin] = override_current_admin
    return app


def test_get_me_returns_current_user(app: FastAPI, user_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    user_use_cases.get_user.return_value = _make_user(is_admin=False)

    response = client.get("/api/v1/users/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "john"


def test_update_me_returns_updated_user(app: FastAPI, user_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    user_use_cases.update_user.return_value = _make_user(is_admin=False)

    response = client.patch("/api/v1/users/me", json={"username": "updated-name"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "john"


def test_delete_me_returns_204(app: FastAPI, user_use_cases: AsyncMock) -> None:
    client = TestClient(app)

    response = client.delete("/api/v1/users/me")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    user_use_cases.delete_user.assert_awaited_once()


def test_admin_get_user_returns_403_for_non_admin_override(app: FastAPI, user_use_cases: AsyncMock) -> None:
    client = TestClient(app)

    async def deny_admin() -> None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    app.dependency_overrides[get_current_admin] = deny_admin

    response = client.get(f"/api/v1/users/{uuid4()}")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    user_use_cases.get_user.assert_not_called()


def test_admin_update_and_delete_user(app: FastAPI, user_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    user_id = uuid4()
    user_use_cases.update_user.return_value = _make_user(is_admin=False)

    update_response = client.patch(f"/api/v1/users/{user_id}", json={"username": "new-name"})
    delete_response = client.delete(f"/api/v1/users/{user_id}")

    assert update_response.status_code == status.HTTP_200_OK
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT


def test_admin_get_user_returns_200(app: FastAPI, user_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    user_id = uuid4()
    user_use_cases.get_user.return_value = _make_user(is_admin=False)

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "john"
