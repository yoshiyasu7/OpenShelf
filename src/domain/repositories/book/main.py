from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from src.domain.entities import Book, BookLoan


class BookRepository(ABC):
    """Abstract repository for book and loan persistence."""

    @abstractmethod
    async def get_by_id(self, *, book_id: UUID) -> Book | None:
        pass

    @abstractmethod
    async def exists_by_title(self, *, title: str, exclude_book_id: UUID | None = None) -> bool:
        pass

    @abstractmethod
    async def create(self, *, data: dict[str, Any]) -> Book:
        pass

    @abstractmethod
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[Book], int]:
        pass

    @abstractmethod
    async def update(self, *, book_id: UUID, data: dict[str, Any]) -> Book | None:
        pass

    @abstractmethod
    async def delete(self, *, book_id: UUID) -> bool:
        pass

    @abstractmethod
    async def has_overdue_loans(self, *, user_id: UUID, as_of: date) -> bool:
        pass

    @abstractmethod
    async def has_open_loan_for_book(self, *, user_id: UUID, book_id: UUID) -> bool:
        pass

    @abstractmethod
    async def take_available_instance(self, *, book_id: UUID) -> Book | None:
        pass

    @abstractmethod
    async def return_instance(self, *, book_id: UUID) -> Book | None:
        pass

    @abstractmethod
    async def create_loan(self, *, user_id: UUID, book_id: UUID, due_date: date) -> BookLoan:
        pass

    @abstractmethod
    async def get_loan_by_id(self, *, loan_id: UUID) -> BookLoan | None:
        pass

    @abstractmethod
    async def mark_loan_returned(self, *, loan_id: UUID) -> BookLoan | None:
        pass

    @abstractmethod
    async def list_open_loans_with_book_titles(self, *, user_id: UUID) -> list[tuple[BookLoan, str | None]]:
        pass
