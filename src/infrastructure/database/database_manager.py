import json
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, override

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.interfaces.database import DatabaseInterface

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


def _json_serializer(obj: object) -> str:
    """Custom JSON serializer that preserves Unicode characteres."""
    return json.dumps(obj, ensure_ascii=False)


class DatabaseManager(DatabaseInterface):
    """PostgreSQL database manager."""

    def __init__(
        self,
        database_url: str,
        debug: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
    ) -> None:
        """Initialize database manager.

        Args:
            database_url: Database connection URL.
            debug: Enable SQL query logging.
            pool_size: Connection pool size.
            max_overflow: Maximum overflow connections.
            pool_recycle: Seconds after which to recycle connections.
        """
        self.database_url = database_url
        self.debug = debug
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self._engine = None
        self._session_factory = None

    @override
    async def initialize(self) -> None:
        """Initialize the database connection and session factory."""
        if self._engine is not None:
            return

        engine_kwargs: dict[str, object] = {
            "echo": self.debug,
            "json_serializer": _json_serializer,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": True,
        }

        engine = create_async_engine(self.database_url, **engine_kwargs)
        self._engine = engine

        self._session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @override
    async def shutdown(self) -> None:
        """Shutdown the database connection."""
        if self._engine is None:
            return

        await self._engine.dispose()
        self._engine = None
        self._session_factory = None

    @override
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        """Get a database session context manager."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self._session_factory() as session:
            yield session

    @override
    async def health_check(self) -> dict[str, object]:
        """Check if the database is healthy and accessible."""
        if self._engine is None:
            return {}

        pool = self._engine.pool
        return {
            "pool_size": pool.size(),  # pyright: ignore[reportAttributeAccessIssue]
            "checked_in": pool.checkedin(),  # pyright: ignore[reportAttributeAccessIssue]
            "checked_out": pool.checkedout(),  # pyright: ignore[reportAttributeAccessIssue]
            "overflow": pool.overflow(),  # pyright: ignore[reportAttributeAccessIssue]
            "invalid": pool.invalid(),  # pyright: ignore[reportAttributeAccessIssue]
        }

    @override
    def __repr__(self) -> str:
        return f"DatabaseManager(PostgreSQL, url={self.database_url})"
