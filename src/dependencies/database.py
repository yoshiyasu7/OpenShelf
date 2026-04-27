"""Database and sessions dependencies."""

from typing import TYPE_CHECKING, Annotated, Protocol

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.provider import get_db_manager

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from contextlib import AbstractAsyncContextManager


# --- CORE DEPENDENCIES ---

class DatabaseProvider(Protocol):
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession]: ...


def get_db_provider() -> DatabaseProvider:
    return get_db_manager()


DBProviderDep = Annotated[DatabaseProvider, Depends(get_db_provider)]


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


# --- PUBLIC TYPE ALIASES ---

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
TxSessionDep = Annotated[AsyncSession, Depends(get_transactional_session)]
