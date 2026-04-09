from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


class SessionRepository(ABC):
    """Abstract repository for session persistence."""

    @abstractmethod
    async def create(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        pass

    @abstractmethod
    async def is_active(self, *, token_hash: str, now: datetime) -> bool:
        pass

    @abstractmethod
    async def revoke(self, *, token_hash: str, now: datetime) -> None:
        pass

    @abstractmethod
    async def revoke_for_user(self, *, user_id: UUID, token_hash: str, now: datetime) -> bool:
        pass
