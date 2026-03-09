"""Database interface."""

import typing as t
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession


class DatabaseInterface(ABC):
    """Abstract database interface."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the database connection and session factory."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the database connection."""
        pass

    @abstractmethod
    @asynccontextmanager
    async def get_session(self) -> t.AsyncGenerator[AsyncSession, None]:
        """Get a database session context manager."""
        pass

    @abstractmethod
    async def health_check(self) -> t.Dict[str, t.Any]:
        """Check if the database is healthy and accessible."""
        pass