from unittest.mock import AsyncMock

from src.dependencies.infrastructure import (
    get_author_repository,
    get_book_repository,
    get_refresh_store,
    get_token_service,
    get_user_repository,
)
from src.infrastructure.repositories.sqlalchemy_author_repository import SQLAlchemyAuthorRepository
from src.infrastructure.repositories.sqlalchemy_book_repository import SQLAlchemyBookRepository
from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.infrastructure.services.jwt import JWTService
from src.infrastructure.settings.main import JWTSettings


def test_get_token_service_uses_nested_jwt_settings() -> None:
    settings = type("Settings", (), {"jwt": JWTSettings("secret", "HS256", 10, 3)})()

    service = get_token_service(settings=settings)

    assert isinstance(service, JWTService)
    assert service.settings.algorithm == "HS256"


def test_get_refresh_store_builds_store_with_session_repo() -> None:
    session = AsyncMock()

    store = get_refresh_store(session=session)

    assert callable(store.create)
    assert callable(store.rotate)
    assert callable(store.revoke)


def test_get_author_user_book_repositories() -> None:
    session = AsyncMock()

    assert isinstance(get_author_repository(session=session), SQLAlchemyAuthorRepository)
    assert isinstance(get_user_repository(session=session), SQLAlchemyUserRepository)
    assert isinstance(get_book_repository(session=session), SQLAlchemyBookRepository)
