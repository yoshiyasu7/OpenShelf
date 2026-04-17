from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.book.main import CreateBookRequest
from src.application.use_cases.book_use_cases import BookUseCases
from src.domain.exceptions.author import AuthorNotFoundError
from src.domain.exceptions.book import InvalidPublicationDateError
from src.domain.exceptions.loan import AlreadyReturnedError, LoanLimitExceededError, NoAvailableInstancesError
from src.domain.repositories.author.main import AuthorRepository
from src.domain.repositories.book.main import BookRepository
from src.domain.repositories.user.main import UserRepository
from tests.helpers import make_author_model, make_book_loan_model, make_book_model


@pytest.fixture
def book_repo() -> AsyncMock:
    return AsyncMock(spec=BookRepository)


@pytest.fixture
def user_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def author_repo() -> AsyncMock:
    return AsyncMock(spec=AuthorRepository)


@pytest.fixture
def use_cases(book_repo: AsyncMock, user_repo: AsyncMock, author_repo: AsyncMock) -> BookUseCases:
    return BookUseCases(
        book_repository=book_repo,
        user_repository=user_repo,
        author_repository=author_repo,
    )


@pytest.mark.asyncio
async def test_create_book_raises_on_invalid_publication_date(use_cases: BookUseCases) -> None:
    payload = CreateBookRequest(
        title="Future Book",
        description="Description",
        publication_date="2400-01-01",
        genres=["fantasy"],
        author_ids=[uuid4()],
        available_instances=1,
    )

    with pytest.raises(InvalidPublicationDateError):
        await use_cases.create_book(payload=payload)


@pytest.mark.asyncio
async def test_create_book_raises_when_author_missing(
    use_cases: BookUseCases,
    book_repo: AsyncMock,
    author_repo: AsyncMock,
) -> None:
    payload = CreateBookRequest(
        title="War and Peace",
        description="Description",
        publication_date="1869-01-01",
        genres=["classic"],
        author_ids=[uuid4()],
        available_instances=1,
    )
    book_repo.exists_by_title.return_value = False
    author_repo.get_by_ids.return_value = []

    with pytest.raises(AuthorNotFoundError):
        await use_cases.create_book(payload=payload)


@pytest.mark.asyncio
async def test_create_book_creates_entity_with_author_relation(
    use_cases: BookUseCases,
    book_repo: AsyncMock,
    author_repo: AsyncMock,
) -> None:
    author_id = uuid4()
    payload = CreateBookRequest(
        title="War and Peace",
        description="Description",
        publication_date="1869-01-01",
        genres=["classic"],
        author_ids=[author_id],
        available_instances=1,
    )
    created_book = make_book_model()
    author_repo.get_by_ids.return_value = [make_author_model(author_id=author_id)]
    book_repo.exists_by_title.return_value = False
    book_repo.create.return_value = created_book

    result = await use_cases.create_book(payload=payload)

    assert result == created_book
    create_call_data = book_repo.create.call_args.kwargs["data"]
    assert "authors" in create_call_data
    assert len(create_call_data["authors"]) == 1


@pytest.mark.asyncio
async def test_issue_book_raises_when_user_limit_exceeded(
    use_cases: BookUseCases,
    book_repo: AsyncMock,
    user_repo: AsyncMock,
) -> None:
    book_id = uuid4()
    user_id = uuid4()
    user = AsyncMock()
    user.books_on_hand = 5

    book_repo.has_overdue_loans.return_value = False
    user_repo.get_by_id.return_value = user

    with pytest.raises(LoanLimitExceededError):
        await use_cases.issue_book(user_id=user_id, book_id=book_id)


@pytest.mark.asyncio
async def test_issue_book_raises_when_no_available_instances(
    use_cases: BookUseCases,
    book_repo: AsyncMock,
    user_repo: AsyncMock,
) -> None:
    book_id = uuid4()
    user_id = uuid4()
    user = AsyncMock()
    user.books_on_hand = 1
    book = make_book_model(book_id=book_id, available_instances=0)

    book_repo.has_overdue_loans.return_value = False
    user_repo.get_by_id.return_value = user
    book_repo.take_available_instance.return_value = None
    book_repo.get_by_id.return_value = book

    with pytest.raises(NoAvailableInstancesError):
        await use_cases.issue_book(user_id=user_id, book_id=book_id)


@pytest.mark.asyncio
async def test_issue_book_returns_loan_and_available_instances(
    use_cases: BookUseCases,
    book_repo: AsyncMock,
    user_repo: AsyncMock,
) -> None:
    book_id = uuid4()
    user_id = uuid4()
    user = AsyncMock()
    user.books_on_hand = 2
    reserved_book = make_book_model(book_id=book_id, available_instances=3)
    loan = make_book_loan_model(user_id=user_id, book_id=book_id)

    book_repo.has_overdue_loans.return_value = False
    user_repo.get_by_id.return_value = user
    book_repo.take_available_instance.return_value = reserved_book
    user_repo.update.return_value = AsyncMock()
    book_repo.create_loan.return_value = loan

    returned_loan, available_instances = await use_cases.issue_book(user_id=user_id, book_id=book_id)

    assert returned_loan == loan
    assert available_instances == 3


@pytest.mark.asyncio
async def test_return_book_raises_when_already_returned(use_cases: BookUseCases, book_repo: AsyncMock) -> None:
    loan_id = uuid4()
    book_repo.get_loan_by_id.return_value = make_book_loan_model(
        loan_id=loan_id,
        returned_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(AlreadyReturnedError):
        await use_cases.return_book(loan_id=loan_id)
