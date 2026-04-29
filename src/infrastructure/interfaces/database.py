"""Database interface."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

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
    def get_session(self) -> AbstractAsyncContextManager[AsyncSession]:
        """Get a database session context manager."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, object]:
        """Check if the database is healthy and accessible."""
        pass
