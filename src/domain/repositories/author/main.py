from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.entities import Author


class AuthorRepository(ABC):
    """Abstract repository for author persistence."""

    @abstractmethod
    async def get_by_id(self, *, author_id: UUID) -> Author | None:
        pass

    @abstractmethod
    async def get_by_ids(self, *, author_ids: list[UUID]) -> list[Author]:
        pass

    @abstractmethod
    async def exists_by_name(self, *, name: str, exclude_author_id: UUID | None = None) -> bool:
        pass

    @abstractmethod
    async def create(self, *, data: dict[str, Any]) -> Author:
        pass

    @abstractmethod
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[Author], int]:
        pass

    @abstractmethod
    async def update(self, *, author_id: UUID, data: dict[str, Any]) -> Author | None:
        pass

    @abstractmethod
    async def delete(self, *, author_id: UUID) -> bool:
        pass
