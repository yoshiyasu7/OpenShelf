from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
import pytest

from src.dependencies.auth import get_current_admin, get_current_user
from src.dependencies.services import get_author_service
from src.interfaces.api.v1.author.main import router as author_router
from tests.helpers import make_author_model, make_book_model, make_user_public


@pytest.fixture
def author_use_cases() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def app(author_use_cases: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(author_router, prefix="/api/v1")

    async def override_author_service() -> AsyncMock:
        return author_use_cases

    async def override_current_user():
        return make_user_public(is_admin=False)

    async def override_current_admin():
        return make_user_public(is_admin=True)

    app.dependency_overrides[get_author_service] = override_author_service
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_admin] = override_current_admin
    return app


def test_create_author_returns_201(app: FastAPI, author_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    created = make_author_model()
    author_use_cases.create_author.return_value = created

    response = client.post(
        "/api/v1/authors/",
        json={
            "name": "Leo Tolstoy",
            "biography": "Russian writer",
            "birthday": "1828-09-09",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["id"] == str(created.id)
    assert payload["name"] == "Leo Tolstoy"
    assert "books" not in payload


def test_get_authors_list_returns_paginated_response(app: FastAPI, author_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    author = make_author_model(books=[make_book_model()])
    author_use_cases.get_authors_list.return_value = {
        "items": [author],
        "total": 1,
        "limit": 10,
        "offset": 0,
    }

    response = client.get("/api/v1/authors/?limit=10&offset=0&name_query=tol")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == str(author.id)
    assert len(payload["items"][0]["books"]) == 1


def test_update_author_returns_403_when_admin_dependency_fails(
    app: FastAPI,
    author_use_cases: AsyncMock,
) -> None:
    client = TestClient(app)

    async def deny_admin_access():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    app.dependency_overrides[get_current_admin] = deny_admin_access

    response = client.patch(
        f"/api/v1/authors/{uuid4()}",
        json={
            "name": "Updated name",
            "biography": "Updated bio",
            "birthday": str(date(1828, 9, 9)),
        },
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    author_use_cases.update_author.assert_not_called()


def test_delete_author_returns_204(app: FastAPI, author_use_cases: AsyncMock) -> None:
    client = TestClient(app)

    response = client.delete(f"/api/v1/authors/{uuid4()}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    author_use_cases.delete_author.assert_awaited_once()


def test_get_author_returns_200(app: FastAPI, author_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    author = make_author_model(books=[make_book_model()])
    author_use_cases.get_author.return_value = author

    response = client.get(f"/api/v1/authors/{author.id}")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["id"] == str(author.id)
    assert payload["books"][0]["id"] == str(author.books[0].id)


def test_update_author_returns_200(app: FastAPI, author_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    author = make_author_model(name="Lev Tolstoy")
    author_use_cases.update_author.return_value = author

    response = client.patch(
        f"/api/v1/authors/{author.id}",
        json={"name": "Lev Tolstoy"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Lev Tolstoy"
