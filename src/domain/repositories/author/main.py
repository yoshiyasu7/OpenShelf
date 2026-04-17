from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    from src.infrastructure.database.models import AuthorModel


class AuthorRepository(ABC):
    """Abstract repository for author persistence."""

    @abstractmethod
    async def get_by_id(self, *, author_id: UUID) -> AuthorModel | None:
        pass

    @abstractmethod
    async def get_by_ids(self, *, author_ids: list[UUID]) -> list[AuthorModel]:
        pass

    @abstractmethod
    async def exists_by_name(self, *, name: str, exclude_author_id: UUID | None = None) -> bool:
        pass

    @abstractmethod
    async def create(self, *, data: dict[str, Any]) -> AuthorModel:
        pass

    @abstractmethod
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[AuthorModel], int]:
        pass

    @abstractmethod
    async def update(self, *, author_id: UUID, data: dict[str, Any]) -> AuthorModel | None:
        pass

    @abstractmethod
    async def delete(self, *, author_id: UUID) -> bool:
        pass
