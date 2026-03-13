"""FastAPI dependencies for infrastructure services."""

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.interfaces.database import DatabaseInterface
from src.infrastructure.database.database_manager import DatabaseManager  # or an abstract getter


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