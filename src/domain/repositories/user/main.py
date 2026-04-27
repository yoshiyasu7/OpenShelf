from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    from src.infrastructure.database.models import UserModel


class UserRepository(ABC):
    """Abstract repository for user persistence."""

    @abstractmethod
    async def get_by_id(self, *, user_id: UUID) -> UserModel | None:
        pass

    @abstractmethod
    async def get_by_identifier(self, *, identifier: str) -> UserModel | None:
        pass

    @abstractmethod
    async def exists_by_username_or_email(self, *, username: str, email: str | None) -> bool:
        pass

    @abstractmethod
    async def create(
        self, *,
        username: str,
        email: str | None,
        password_hash: str,
        is_admin: bool = False,
    ) -> UserModel:
        pass

    @abstractmethod
    async def update(self, *, user_id: UUID, data: dict[str, Any]) -> UserModel | None:
        pass

    @abstractmethod
    async def delete(self, *, user_id: UUID) -> bool:
        pass
