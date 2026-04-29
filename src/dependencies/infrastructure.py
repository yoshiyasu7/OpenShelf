"""Dependencies of infrastructure services and repositories."""

from typing import Annotated

from fastapi import Depends

from src.application.ports import PasswordHasher, RefreshSessionStore, TokenService
from src.dependencies.database import TxSessionDep  # noqa: TC001
from src.domain.repositories.author.main import AuthorRepository
from src.domain.repositories.book.main import BookRepository
from src.domain.repositories.user.main import UserRepository
from src.infrastructure.auth.passwords import PasswordHasher as Argon2PasswordHasher
from src.infrastructure.auth.refresh_sessions import RefreshSessionStore as RefreshSessionStoreImpl
from src.infrastructure.repositories.sqlalchemy_author_repository import SQLAlchemyAuthorRepository
from src.infrastructure.repositories.sqlalchemy_book_repository import SQLAlchemyBookRepository
from src.infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository
from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.infrastructure.services.jwt import JWTService
from src.infrastructure.settings.main import Settings, get_settings

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_token_service(settings: SettingsDep) -> TokenService:
    return JWTService(settings=settings.jwt)


def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


def get_refresh_store(session: TxSessionDep) -> RefreshSessionStore:
    repo = SQLAlchemySessionRepository(session=session)
    return RefreshSessionStoreImpl(repository=repo)


def get_author_repository(session: TxSessionDep) -> AuthorRepository:
    return SQLAlchemyAuthorRepository(session=session)


def get_user_repository(session: TxSessionDep) -> UserRepository:
    return SQLAlchemyUserRepository(session=session)


def get_book_repository(session: TxSessionDep) -> BookRepository:
    return SQLAlchemyBookRepository(session=session)


# --- PUBLIC TYPE ALIASES ---

TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]
PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
RefreshStoreDep = Annotated[RefreshSessionStore, Depends(get_refresh_store)]
AuthorRepoDep = Annotated[AuthorRepository, Depends(get_author_repository)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
