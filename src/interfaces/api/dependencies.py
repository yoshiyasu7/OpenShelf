"""FastAPI dependencies for infrastructure services."""

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.auth.refresh_sessions import RefreshSessionStore
from src.application.use_cases.auth_use_cases import ValidateAccessTokenUseCase
from src.infrastructure.interfaces.database import DatabaseInterface
from src.infrastructure.database.database_manager import DatabaseManager
from src.infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository
from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.infrastructure.services.jwt import JWTService
from src.infrastructure.settings.main import Settings, get_settings
from src.application.use_cases.auth_use_cases import AuthUseCases


async def get_database_manager(request: Request) -> DatabaseInterface:
    """
    Return the initialized database manager.
    """
    db_manager: DatabaseManager | None = getattr(request.app.state, "db_manager", None)
    if db_manager is None:
        raise RuntimeError("Database manager is not initialized.")
    return db_manager


async def get_db_session(
    db: DatabaseInterface = Depends(get_database_manager),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for a single request.
    
    Usage in route handlers:
        async def handler(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with db.get_session() as session:
        yield session


async def get_transactional_session(
    db: DatabaseInterface = Depends(get_database_manager),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for a single request that will be automatically committed or rolled back.

    Usage in route handlers:
        async def handler(session: AsyncSession = Depends(get_transactional_session)):
            ...
    """
    async with db.get_session() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise


def get_jwt_service(
    settings: Settings = Depends(get_settings),
) -> JWTService:
    """
    Provide configured JWT service instance.
    """
    return JWTService(settings=settings.jwt)


def get_refresh_session_store(
    session: AsyncSession = Depends(get_transactional_session),
) -> RefreshSessionStore:
    """Provide refresh session store with injected dependencies."""
    repository = SQLAlchemySessionRepository(session=session)
    return RefreshSessionStore(repository=repository)


def get_user_repository(
    session: AsyncSession = Depends(get_transactional_session),
) -> SQLAlchemyUserRepository:
    """Provide user repository with injected session."""
    return SQLAlchemyUserRepository(session=session)


def get_auth_use_cases(
    jwt: JWTService = Depends(get_jwt_service),
    user_repository: SQLAlchemyUserRepository = Depends(get_user_repository),
    refresh_store: RefreshSessionStore = Depends(get_refresh_session_store),
) -> AuthUseCases:
    """Provide auth use cases with injected dependencies."""
    return AuthUseCases(user_repository=user_repository, jwt=jwt, refresh_store=refresh_store)


def get_validate_access_token_use_case(
    jwt: JWTService = Depends(get_jwt_service),
    user_repository: SQLAlchemyUserRepository = Depends(get_user_repository),
) -> ValidateAccessTokenUseCase:
    """Provide use case for current user resolution."""
    return ValidateAccessTokenUseCase(jwt=jwt, user_repository=user_repository)
