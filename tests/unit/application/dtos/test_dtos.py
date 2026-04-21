from uuid import uuid4

from src.application.dtos.auth.main import LoginRequest, RefreshRequest, TokenResponse
from src.application.dtos.author.main import CreateAuthorRequest, UpdateAuthorRequest
from src.application.dtos.book.main import CreateBookRequest, UpdateBookRequest
from src.application.dtos.user.main import UserPublic


def test_author_name_normalization_for_create_and_update() -> None:
    create = CreateAuthorRequest(name="  Leo   Tolstoy ", biography="bio", birthday="1828-09-09")
    update_with_none = UpdateAuthorRequest(name=None)

    assert create.name == "Leo Tolstoy"
    assert update_with_none.name is None


def test_book_title_normalization_for_create_and_update() -> None:
    create = CreateBookRequest(
        title="  War   and   Peace ",
        description="desc",
        publication_date="1869-01-01",
        genres=["classic"],
        author_ids=[uuid4()],
        available_instances=1,
    )
    update_with_none = UpdateBookRequest(title=None)

    assert create.title == "War and Peace"
    assert update_with_none.title is None


def test_auth_dtos_validate_and_token_response_defaults() -> None:
    user = UserPublic(id=uuid4(), username="john", email="john@example.com", is_admin=False)
    login = LoginRequest(identifier="john", password="secret123")
    refresh = RefreshRequest(refresh_token="refresh-token-123")
    token_response = TokenResponse(access_token="a", refresh_token="r", user=user)

    assert login.identifier == "john"
    assert refresh.refresh_token.startswith("refresh")
    assert token_response.token_type == "bearer"
