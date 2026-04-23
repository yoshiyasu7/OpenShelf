from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from src.domain.exceptions.author import AuthorNotFoundError
from src.domain.exceptions.book import BookAlreadyExistsError, BookNotFoundError, InvalidPublicationDateError
from src.domain.exceptions.loan import (
    AlreadyBorrowingBookError,
    AlreadyReturnedError,
    ConcurrencyConflictError,
    LoanLimitExceededError,
    LoanNotFoundError,
    LoanOverdueError,
    NoAvailableInstancesError,
)
from src.domain.exceptions.user import UserNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.dtos.book.main import CreateBookRequest, UpdateBookRequest
    from src.application.dtos.main import QueryFilterParams
    from src.domain.repositories.author.main import AuthorRepository
    from src.domain.repositories.book.main import BookRepository
    from src.domain.repositories.user.main import UserRepository
    from src.infrastructure.database.models import BookLoanModel, BookModel

MAX_BOOKS_ON_HAND = 5
DEFAULT_LOAN_DAYS = 14
MIN_PUBLICATION_YEAR = 1440


class BookUseCases:
    """Core logic for managing books and book loans."""

    def __init__(
        self,
        *,
        book_repository: BookRepository,
        user_repository: UserRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._book_repository = book_repository
        self._user_repository = user_repository
        self._author_repository = author_repository

    async def create_book(self, *, payload: CreateBookRequest) -> BookModel:
        create_data = payload.model_dump()
        self._validate_publication_date(publication_date=create_data["publication_date"])

        if await self._book_repository.exists_by_title(title=create_data["title"]):
            raise BookAlreadyExistsError()

        author_ids = create_data.pop("author_ids")
        authors = await self._author_repository.get_by_ids(author_ids=author_ids)
        if len(authors) != len(set(author_ids)):
            raise AuthorNotFoundError("One or more authors from author_ids were not found")

        create_data["authors"] = authors
        return await self._book_repository.create(data=create_data)

    async def get_book(self, *, book_id: UUID) -> BookModel:
        book = await self._book_repository.get_by_id(book_id=book_id)
        if not book:
            raise BookNotFoundError(f"Book with id {book_id} not found")
        return book

    async def get_books_list(self, *, filters: QueryFilterParams) -> dict[str, Any]:
        items, total = await self._book_repository.list_paginated(
            limit=filters.limit,
            offset=filters.offset,
            name_query=filters.name_query,
        )
        return {
            "items": items,
            "total": total,
            "limit": filters.limit,
            "offset": filters.offset,
        }

    async def update_book(self, *, book_id: UUID, payload: UpdateBookRequest) -> BookModel:
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_book(book_id=book_id)

        publication_date = update_data.get("publication_date")
        if publication_date is not None:
            self._validate_publication_date(publication_date=publication_date)

        new_title = update_data.get("title")
        if new_title and await self._book_repository.exists_by_title(title=new_title, exclude_book_id=book_id):
            raise BookAlreadyExistsError()

        updated_book = await self._book_repository.update(book_id=book_id, data=update_data)
        if not updated_book:
            raise BookNotFoundError(f"Book with id {book_id} not found")
        return updated_book

    async def delete_book(self, *, book_id: UUID) -> None:
        deleted = await self._book_repository.delete(book_id=book_id)
        if not deleted:
            raise BookNotFoundError(f"Book with id {book_id} not found")

    async def issue_book(self, *, user_id: UUID, book_id: UUID) -> tuple[BookLoanModel, int]:
        current_date = self._utc_today()
        if await self._book_repository.has_overdue_loans(user_id=user_id, as_of=current_date):
            raise LoanOverdueError()

        user = await self._user_repository.get_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        if user.books_on_hand >= MAX_BOOKS_ON_HAND:
            raise LoanLimitExceededError()
        if await self._book_repository.has_open_loan_for_book(user_id=user_id, book_id=book_id):
            raise AlreadyBorrowingBookError()

        reserved_book = await self._book_repository.take_available_instance(book_id=book_id)
        if not reserved_book:
            found_book = await self._book_repository.get_by_id(book_id=book_id)
            if not found_book:
                raise BookNotFoundError(f"Book with id {book_id} not found")
            if found_book.available_instances <= 0:
                raise NoAvailableInstancesError()
            raise ConcurrencyConflictError()

        updated_user = await self._user_repository.update(
            user_id=user_id,
            data={"books_on_hand": user.books_on_hand + 1},
        )
        if not updated_user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        due_date = current_date + timedelta(days=DEFAULT_LOAN_DAYS)
        loan = await self._book_repository.create_loan(user_id=user_id, book_id=book_id, due_date=due_date)
        return loan, reserved_book.available_instances

    async def return_book(self, *, loan_id: UUID) -> tuple[BookLoanModel, int]:
        loan = await self._book_repository.get_loan_by_id(loan_id=loan_id)
        if not loan:
            raise LoanNotFoundError(f"Loan with id {loan_id} not found")
        if loan.returned_at is not None:
            raise AlreadyReturnedError()

        closed_loan = await self._book_repository.mark_loan_returned(loan_id=loan_id)
        if not closed_loan:
            raise ConcurrencyConflictError()

        returned_book = await self._book_repository.return_instance(book_id=loan.book_id)
        if not returned_book:
            raise BookNotFoundError(f"Book with id {loan.book_id} not found")

        borrower = await self._user_repository.get_by_id(user_id=loan.user_id)
        if borrower and borrower.books_on_hand > 0:
            await self._user_repository.update(
                user_id=loan.user_id,
                data={"books_on_hand": borrower.books_on_hand - 1},
            )

        return closed_loan, returned_book.available_instances

    def _validate_publication_date(self, *, publication_date: date) -> None:
        if publication_date > self._utc_today() or publication_date.year < MIN_PUBLICATION_YEAR:
            raise InvalidPublicationDateError()

    @staticmethod
    def _utc_today() -> date:
        return datetime.now(tz=UTC).date()
