from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
import pytest

from src.dependencies.auth import get_current_admin, get_current_user
from src.dependencies.services import get_book_service
from src.interfaces.api.v1.book.main import router as book_router
from tests.helpers import make_author_model, make_book_loan_model, make_book_model, make_user_public


@pytest.fixture
def book_use_cases() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def app(book_use_cases: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(book_router, prefix="/api/v1")

    async def override_book_service() -> AsyncMock:
        return book_use_cases

    async def override_current_user():
        return make_user_public(is_admin=False)

    async def override_current_admin():
        return make_user_public(is_admin=True)

    app.dependency_overrides[get_book_service] = override_book_service
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_current_admin] = override_current_admin
    return app


def test_create_book_returns_201(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    created = make_book_model(authors=[make_author_model()])
    book_use_cases.create_book.return_value = created

    response = client.post(
        "/api/v1/books/",
        json={
            "title": "War and Peace",
            "description": "Classic novel",
            "publication_date": "1869-01-01",
            "genres": ["classic"],
            "author_ids": [str(uuid4())],
            "available_instances": 3,
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["id"] == str(created.id)
    assert payload["title"] == "War and Peace"
    assert len(payload["authors"]) == 1


def test_issue_book_returns_201(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    book_id = uuid4()
    loan = make_book_loan_model(book_id=book_id)
    book_use_cases.issue_book.return_value = (loan, 2)

    response = client.post(f"/api/v1/books/{book_id}/issue")

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload["loan"]["id"] == str(loan.id)
    assert payload["available_instances"] == 2


def test_return_book_returns_200(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    loan_id = uuid4()
    loan = make_book_loan_model(loan_id=loan_id)
    book_use_cases.return_book.return_value = (loan, 4)

    response = client.post(f"/api/v1/books/loans/{loan_id}/return")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["loan"]["id"] == str(loan.id)
    assert payload["available_instances"] == 4
