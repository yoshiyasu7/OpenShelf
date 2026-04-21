from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infrastructure.repositories.sqlalchemy_book_repository import SQLAlchemyBookRepository
from tests.helpers import make_book_loan_model, make_book_model


@pytest.fixture
def session() -> AsyncMock:
    session_mock = AsyncMock()
    session_mock.add = Mock()
    return session_mock


@pytest.fixture
def repository(session: AsyncMock) -> SQLAlchemyBookRepository:
    return SQLAlchemyBookRepository(session=session)


@pytest.mark.asyncio
async def test_exists_by_title_adds_exclude_filter_when_passed(
    repository: SQLAlchemyBookRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result
    book_id = uuid4()

    exists = await repository.exists_by_title(title="War and Peace", exclude_book_id=book_id)

    assert exists is True
    statement = session.execute.call_args.args[0]
    statement_text = str(statement)
    assert "lower(books.title)" in statement_text
    assert "books.id !=" in statement_text


@pytest.mark.asyncio
async def test_take_available_instance_uses_positive_instances_filter(
    repository: SQLAlchemyBookRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = make_book_model(available_instances=2)
    session.execute.return_value = result

    await repository.take_available_instance(book_id=uuid4())

    statement = session.execute.call_args.args[0]
    statement_text = str(statement)
    assert "books.available_instances >" in statement_text
    assert "books.available_instances - :available_instances_1" in statement_text


@pytest.mark.asyncio
async def test_list_paginated_returns_rows_and_total(
    repository: SQLAlchemyBookRepository,
    session: AsyncMock,
) -> None:
    book = make_book_model()
    result = Mock()
    result.all.return_value = [(book, 9)]
    session.execute.return_value = result

    books, total = await repository.list_paginated(limit=3, offset=0, name_query="war")

    assert books == [book]
    assert total == 9
    statement = session.execute.call_args.args[0]
    statement_text = str(statement)
    assert "ORDER BY books.title ASC, books.id ASC" in statement_text
    assert "count(*) OVER ()" in statement_text


@pytest.mark.asyncio
async def test_has_overdue_loans_returns_false_when_not_found(
    repository: SQLAlchemyBookRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    has_overdue = await repository.has_overdue_loans(user_id=uuid4(), as_of=date.today())

    assert has_overdue is False


@pytest.mark.asyncio
async def test_get_by_id_returns_book(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    book = make_book_model()
    result = Mock()
    result.scalar_one_or_none.return_value = book
    session.execute.return_value = result

    found = await repository.get_by_id(book_id=book.id)

    assert found == book


@pytest.mark.asyncio
async def test_create_persists_and_returns_book(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    data = {
        "title": "War and Peace",
        "description": "Classic novel",
        "publication_date": date(1869, 1, 1),
        "genres": ["classic"],
        "available_instances": 3,
    }

    created = await repository.create(data=data)

    assert created.title == "War and Peace"
    session.add.assert_called_once_with(created)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_paginated_returns_empty_payload(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    result = Mock()
    result.all.return_value = []
    session.execute.return_value = result

    books, total = await repository.list_paginated(limit=1, offset=0, name_query=None)

    assert books == []
    assert total == 0


@pytest.mark.asyncio
async def test_update_returns_book(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    updated_book = make_book_model(title="Updated")
    result = Mock()
    result.scalar_one_or_none.return_value = updated_book
    session.execute.return_value = result

    updated = await repository.update(book_id=uuid4(), data={"title": "Updated"})

    assert updated == updated_book


@pytest.mark.asyncio
async def test_delete_returns_true_when_row_deleted(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result

    deleted = await repository.delete(book_id=uuid4())

    assert deleted is True


@pytest.mark.asyncio
async def test_return_instance_returns_updated_book(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    returned = make_book_model(available_instances=4)
    result = Mock()
    result.scalar_one_or_none.return_value = returned
    session.execute.return_value = result

    book = await repository.return_instance(book_id=uuid4())

    assert book == returned


@pytest.mark.asyncio
async def test_create_loan_persists_and_returns_model(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    user_id = uuid4()
    book_id = uuid4()
    due_date = date(2026, 5, 1)

    loan = await repository.create_loan(user_id=user_id, book_id=book_id, due_date=due_date)

    assert loan.user_id == user_id
    assert loan.book_id == book_id
    assert loan.due_date == due_date
    session.add.assert_called_once_with(loan)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_loan_by_id_returns_loan(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    loan = make_book_loan_model()
    result = Mock()
    result.scalar_one_or_none.return_value = loan
    session.execute.return_value = result

    found = await repository.get_loan_by_id(loan_id=loan.id)

    assert found == loan


@pytest.mark.asyncio
async def test_get_open_loan_by_id_returns_loan(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    loan = make_book_loan_model()
    result = Mock()
    result.scalar_one_or_none.return_value = loan
    session.execute.return_value = result

    found = await repository.get_open_loan_by_id(loan_id=loan.id)

    assert found == loan


@pytest.mark.asyncio
async def test_mark_loan_returned_returns_updated_loan(repository: SQLAlchemyBookRepository, session: AsyncMock) -> None:
    loan = make_book_loan_model()
    result = Mock()
    result.scalar_one_or_none.return_value = loan
    session.execute.return_value = result

    updated = await repository.mark_loan_returned(loan_id=loan.id)

    assert updated == loan
