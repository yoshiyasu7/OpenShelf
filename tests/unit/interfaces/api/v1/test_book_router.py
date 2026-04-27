from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.application.dtos.main import PaginatedResult
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
    assert payload["loan"]["issued_at"] is not None
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
    assert payload["loan"]["issued_at"] is not None
    assert payload["available_instances"] == 4


def test_get_books_list_returns_200(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    book = make_book_model(authors=[make_author_model()])
    book_use_cases.get_books_list.return_value = PaginatedResult(items=[book], total=1, limit=10, offset=0)

    response = client.get("/api/v1/books/?limit=10&offset=0")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["items"][0]["id"] == str(book.id)
    assert payload["items"][0]["authors"][0]["id"] == str(book.authors[0].id)


def test_get_book_returns_200(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    book = make_book_model(authors=[make_author_model()])
    book_use_cases.get_book.return_value = book

    response = client.get(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(book.id)


def test_update_book_returns_200(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    book = make_book_model(authors=[make_author_model()], title="Updated title")
    book_use_cases.update_book.return_value = book

    response = client.patch(f"/api/v1/books/{book.id}", json={"title": "Updated title"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "Updated title"


def test_delete_book_returns_204(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)

    response = client.delete(f"/api/v1/books/{uuid4()}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    book_use_cases.delete_book.assert_awaited_once()


def test_get_my_open_loans_returns_200(app: FastAPI, book_use_cases: AsyncMock) -> None:
    client = TestClient(app)
    loan = make_book_loan_model()
    book_use_cases.get_open_loans_for_user.return_value = [
        {
            "loan_id": loan.id,
            "book_id": loan.book_id,
            "title": "War and Peace",
            "issued_at": loan.issued_at,
            "due_date": loan.due_date,
        }
    ]

    response = client.get("/api/v1/books/loans/me")

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload[0]["loan_id"] == str(loan.id)
    assert payload[0]["title"] == "War and Peace"
