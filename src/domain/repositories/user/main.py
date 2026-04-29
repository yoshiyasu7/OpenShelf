from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.entities import User


class UserRepository(ABC):
    """Abstract repository for user persistence."""

    @abstractmethod
    async def get_by_id(self, *, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def get_by_identifier(self, *, identifier: str) -> User | None:
        pass

    @abstractmethod
    async def exists_by_username_or_email(self, *, username: str, email: str | None) -> bool:
        pass

    @abstractmethod
    async def create(
        self,
        *,
        username: str,
        email: str | None,
        password_hash: str,
        is_admin: bool = False,
    ) -> User:
        pass

    @abstractmethod
    async def update(self, *, user_id: UUID, data: dict[str, Any]) -> User | None:
        pass

    @abstractmethod
    async def increment_books_on_hand(self, *, user_id: UUID, max_books_on_hand: int) -> User | None:
        pass

    @abstractmethod
    async def decrement_books_on_hand(self, *, user_id: UUID) -> User | None:
        pass

    @abstractmethod
    async def delete(self, *, user_id: UUID) -> bool:
        pass
