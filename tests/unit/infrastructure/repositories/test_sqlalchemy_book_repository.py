from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infrastructure.repositories.sqlalchemy_book_repository import SQLAlchemyBookRepository
from tests.helpers import make_book_model


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


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
