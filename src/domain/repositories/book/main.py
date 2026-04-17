from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from src.infrastructure.database.models import BookLoanModel, BookModel


class BookRepository(ABC):
    """Abstract repository for book and loan persistence."""

    @abstractmethod
    async def get_by_id(self, *, book_id: UUID) -> BookModel | None:
        pass

    @abstractmethod
    async def exists_by_title(self, *, title: str, exclude_book_id: UUID | None = None) -> bool:
        pass

    @abstractmethod
    async def create(self, *, data: dict[str, Any]) -> BookModel:
        pass

    @abstractmethod
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[BookModel], int]:
        pass

    @abstractmethod
    async def update(self, *, book_id: UUID, data: dict[str, Any]) -> BookModel | None:
        pass

    @abstractmethod
    async def delete(self, *, book_id: UUID) -> bool:
        pass

    @abstractmethod
    async def has_overdue_loans(self, *, user_id: UUID, as_of: date) -> bool:
        pass

    @abstractmethod
    async def take_available_instance(self, *, book_id: UUID) -> BookModel | None:
        pass

    @abstractmethod
    async def return_instance(self, *, book_id: UUID) -> BookModel | None:
        pass

    @abstractmethod
    async def create_loan(self, *, user_id: UUID, book_id: UUID, due_date: date) -> BookLoanModel:
        pass

    @abstractmethod
    async def get_loan_by_id(self, *, loan_id: UUID) -> BookLoanModel | None:
        pass

    @abstractmethod
    async def get_open_loan_by_id(self, *, loan_id: UUID) -> BookLoanModel | None:
        pass

    @abstractmethod
    async def mark_loan_returned(self, *, loan_id: UUID) -> BookLoanModel | None:
        pass
