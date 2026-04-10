"""Dependencies of infrastructure services and repositories."""
from typing import Annotated

from fastapi import Depends

from src.dependencies.database import TxSessionDep  # noqa: TC001
from src.infrastructure.auth.refresh_sessions import RefreshSessionStore
from src.infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository
from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from src.infrastructure.services.jwt import JWTService
from src.infrastructure.settings.main import Settings, get_settings

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_jwt_service(settings: SettingsDep) -> JWTService:
    return JWTService(settings=settings.jwt)


def get_refresh_store(session: TxSessionDep) -> RefreshSessionStore:
    repo = SQLAlchemySessionRepository(session=session)
    return RefreshSessionStore(repository=repo)


def get_user_repository(session: TxSessionDep) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session=session)


# --- PUBLIC TYPE ALIASES ---

JWTDep = Annotated[JWTService, Depends(get_jwt_service)]
RefreshStoreDep = Annotated[RefreshSessionStore, Depends(get_refresh_store)]
UserRepoDep = Annotated[SQLAlchemyUserRepository, Depends(get_user_repository)]
