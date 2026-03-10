"""FastAPI dependencies for infrastructure services."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.interfaces.database import DatabaseInterface
from src.infrastructure.database.database_manager import DatabaseManager  # or an abstract getter


# In a simple setup, we keep a single global DatabaseManager instance.
_db_manager: DatabaseManager | None = None


async def get_database_manager() -> DatabaseInterface:
    """
    Return the initialized database manager.

    This function expects the manager to be created and initialized
    during application startup (lifespan). If it is missing, it means
    the app was not configured correctly.
    """
    if _db_manager is None:
        raise RuntimeError("Database manager is not initialized.")
    return _db_manager


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