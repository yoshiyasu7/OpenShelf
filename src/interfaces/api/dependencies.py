from typing import TYPE_CHECKING, Annotated, Protocol

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.auth_use_cases import AuthUseCases, ValidateAccessTokenUseCase
from src.infrastructure.auth.refresh_sessions import RefreshSessionStore
from src.infrastructure.database.provider import get_db_manager
from src.infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository
from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.infrastructure.services.jwt import JWTService
from src.infrastructure.settings.main import Settings, get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from contextlib import AbstractAsyncContextManager

# --- INTERFACES ---

class DatabaseProvider(Protocol):
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


# --- CORE DEPENDENCIES ---

def get_db_provider() -> DatabaseProvider:
    return get_db_manager()


DBProviderDep = Annotated[DatabaseProvider, Depends(get_db_provider)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


# --- DATABASE SESSIONS ---

async def get_db_session(
    provider: DBProviderDep,
) -> AsyncGenerator[AsyncSession]:
    async with provider.get_session() as session:
        yield session


async def get_transactional_session(
    provider: DBProviderDep,
) -> AsyncGenerator[AsyncSession]:
    async with provider.get_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
TxSessionDep = Annotated[AsyncSession, Depends(get_transactional_session)]


# --- INFRASTRUCTURE SERVICES ---

def get_jwt_service(settings: SettingsDep) -> JWTService:
    return JWTService(settings=settings.jwt)


def get_user_repository(session: TxSessionDep) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session=session)


def get_refresh_store(session: TxSessionDep) -> RefreshSessionStore:
    repo = SQLAlchemySessionRepository(session=session)
    return RefreshSessionStore(repository=repo)


# --- USE CASES ---

def get_auth_service(
    jwt: Annotated[JWTService, Depends(get_jwt_service)],
    user_repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
    refresh_store: Annotated[RefreshSessionStore, Depends(get_refresh_store)],
) -> AuthUseCases:
    return AuthUseCases(
        user_repository=user_repo,
        jwt=jwt,
        refresh_store=refresh_store,
    )


def get_validate_token_service(
    jwt: Annotated[JWTService, Depends(get_jwt_service)],
    user_repo: Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)],
) -> ValidateAccessTokenUseCase:
    return ValidateAccessTokenUseCase(jwt=jwt, user_repository=user_repo)


# --- PUBLIC TYPE ALIASES ---

AuthService = Annotated[AuthUseCases, Depends(get_auth_service)]
ValidateTokenService = Annotated[ValidateAccessTokenUseCase, Depends(get_validate_token_service)]
DBSession = SessionDep
