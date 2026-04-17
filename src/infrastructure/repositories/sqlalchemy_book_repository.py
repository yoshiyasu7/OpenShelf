from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, override

from sqlalchemy import delete, func, select, update

from src.domain.repositories.book.main import BookRepository
from src.infrastructure.database.models import BookLoanModel, BookModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyBookRepository(BookRepository):
    """SQLAlchemy repository for book reads and loan operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def get_by_id(self, *, book_id: UUID) -> BookModel | None:
        stmt = select(BookModel).where(BookModel.id == book_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def exists_by_title(self, *, title: str, exclude_book_id: UUID | None = None) -> bool:
        normalized_title = title.strip()
        stmt = select(BookModel.id).where(func.lower(BookModel.title) == normalized_title.lower())
        if exclude_book_id is not None:
            stmt = stmt.where(BookModel.id != exclude_book_id)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def create(self, *, data: dict[str, Any]) -> BookModel:
        book = BookModel(**data)
        self._session.add(book)
        await self._session.flush()
        return book

    @override
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[BookModel], int]:
        stmt = (
            select(BookModel, func.count().over().label("total_count"))
            .order_by(BookModel.title.asc(), BookModel.id.asc())
            .limit(limit)
            .offset(offset)
        )
        if name_query:
            normalized_query = name_query.strip()
            stmt = stmt.where(BookModel.title.ilike(f"%{normalized_query}%"))

        result = await self._session.execute(stmt)
        rows = result.all()
        if not rows:
            return [], 0

        books = [row[0] for row in rows]
        total_count = int(rows[0][1])
        return books, total_count

    @override
    async def update(self, *, book_id: UUID, data: dict[str, Any]) -> BookModel | None:
        stmt = (
            update(BookModel)
            .where(BookModel.id == book_id)
            .values(**data)
            .returning(BookModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def delete(self, *, book_id: UUID) -> bool:
        stmt = delete(BookModel).where(BookModel.id == book_id).returning(BookModel.id)
        result = await self._session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    @override
    async def has_overdue_loans(self, *, user_id: UUID, as_of: date) -> bool:
        stmt = (
            select(BookLoanModel.id)
            .where(
                BookLoanModel.user_id == user_id,
                BookLoanModel.returned_at.is_(None),
                BookLoanModel.due_date < as_of,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def take_available_instance(self, *, book_id: UUID) -> BookModel | None:
        stmt = (
            update(BookModel)
            .where(BookModel.id == book_id, BookModel.available_instances > 0)
            .values(available_instances=BookModel.available_instances - 1)
            .returning(BookModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def return_instance(self, *, book_id: UUID) -> BookModel | None:
        stmt = (
            update(BookModel)
            .where(BookModel.id == book_id)
            .values(available_instances=BookModel.available_instances + 1)
            .returning(BookModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def create_loan(self, *, user_id: UUID, book_id: UUID, due_date: date) -> BookLoanModel:
        loan = BookLoanModel(
            user_id=user_id,
            book_id=book_id,
            due_date=due_date,
        )
        self._session.add(loan)
        await self._session.flush()
        return loan

    @override
    async def get_loan_by_id(self, *, loan_id: UUID) -> BookLoanModel | None:
        stmt = select(BookLoanModel).where(BookLoanModel.id == loan_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def get_open_loan_by_id(self, *, loan_id: UUID) -> BookLoanModel | None:
        stmt = select(BookLoanModel).where(BookLoanModel.id == loan_id, BookLoanModel.returned_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def mark_loan_returned(self, *, loan_id: UUID) -> BookLoanModel | None:
        stmt = (
            update(BookLoanModel)
            .where(BookLoanModel.id == loan_id, BookLoanModel.returned_at.is_(None))
            .values(returned_at=datetime.now(tz=UTC))
            .returning(BookLoanModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
