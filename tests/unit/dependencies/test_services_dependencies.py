from unittest.mock import AsyncMock, Mock

from src.application.use_cases.auth_use_cases import AuthUseCases, ValidateAccessTokenUseCase
from src.application.use_cases.author_use_cases import AuthorUseCases
from src.application.use_cases.book_use_cases import BookUseCases
from src.application.use_cases.user_use_cases import UserUseCases
from src.dependencies.services import (
    get_auth_service,
    get_author_service,
    get_book_service,
    get_user_service,
    get_validate_token_service,
)


def test_get_auth_service_returns_auth_use_cases() -> None:
    service = get_auth_service(jwt=Mock(), user_repo=AsyncMock(), refresh_store=AsyncMock())
    assert isinstance(service, AuthUseCases)


def test_get_author_service_returns_author_use_cases() -> None:
    service = get_author_service(author_repo=AsyncMock())
    assert isinstance(service, AuthorUseCases)


def test_get_user_service_returns_user_use_cases() -> None:
    service = get_user_service(user_repo=AsyncMock())
    assert isinstance(service, UserUseCases)


def test_get_book_service_returns_book_use_cases() -> None:
    service = get_book_service(book_repo=AsyncMock(), user_repo=AsyncMock(), author_repo=AsyncMock())
    assert isinstance(service, BookUseCases)


def test_get_validate_token_service_returns_use_case() -> None:
    service = get_validate_token_service(jwt=Mock(), user_repo=AsyncMock())
    assert isinstance(service, ValidateAccessTokenUseCase)
