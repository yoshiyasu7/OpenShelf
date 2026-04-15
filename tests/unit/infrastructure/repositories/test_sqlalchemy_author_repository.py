from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infrastructure.repositories.sqlalchemy_author_repository import SQLAlchemyAuthorRepository
from tests.helpers import make_author_model


@pytest.fixture
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def repository(session: AsyncMock) -> SQLAlchemyAuthorRepository:
    return SQLAlchemyAuthorRepository(session=session)


@pytest.mark.asyncio
async def test_exists_by_name_adds_exclude_filter_when_passed(
    repository: SQLAlchemyAuthorRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result
    author_id = uuid4()

    exists = await repository.exists_by_name(name="Leo Tolstoy", exclude_author_id=author_id)

    assert exists is True
    statement = session.execute.call_args.args[0]
    statement_text = str(statement)
    assert "lower(authors.name)" in statement_text
    assert "authors.id !=" in statement_text


@pytest.mark.asyncio
async def test_list_paginated_returns_empty_payload_when_no_rows(
    repository: SQLAlchemyAuthorRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.all.return_value = []
    session.execute.return_value = result

    authors, total = await repository.list_paginated(limit=10, offset=0, name_query=None)

    assert authors == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_paginated_returns_rows_and_total(
    repository: SQLAlchemyAuthorRepository,
    session: AsyncMock,
) -> None:
    author = make_author_model()
    result = Mock()
    result.all.return_value = [(author, 17)]
    session.execute.return_value = result

    authors, total = await repository.list_paginated(limit=5, offset=10, name_query="tol")

    assert authors == [author]
    assert total == 17
    statement = session.execute.call_args.args[0]
    statement_text = str(statement)
    assert "count(*) OVER ()" in statement_text
    assert "ORDER BY authors.name ASC, authors.id ASC" in statement_text


@pytest.mark.asyncio
async def test_delete_returns_false_when_nothing_deleted(
    repository: SQLAlchemyAuthorRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    deleted = await repository.delete(author_id=uuid4())

    assert deleted is False
