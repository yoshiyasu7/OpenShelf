from __future__ import annotations

from abc import ABC, abstractmethod
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
        self,
        *,
        username: str,
        email: str | None,
        password_hash: str,
        is_admin: bool = False,
    ) -> UserModel:
        pass
