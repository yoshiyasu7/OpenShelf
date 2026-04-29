from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infrastructure.repositories.sqlalchemy_author_repository import SQLAlchemyAuthorRepository
from tests.helpers import make_author_model


@pytest.fixture
def session() -> AsyncMock:
    session_mock = AsyncMock()
    session_mock.add = Mock()
    return session_mock


@pytest.fixture
def repository(session: AsyncMock) -> SQLAlchemyAuthorRepository:
    return SQLAlchemyAuthorRepository(session=session)


@pytest.mark.asyncio
async def test_get_by_ids_returns_entities(
    repository: SQLAlchemyAuthorRepository,
    session: AsyncMock,
) -> None:
    author = make_author_model()
    result = Mock()
    scalars = Mock()
    scalars.all.return_value = [author]
    result.scalars.return_value = scalars
    session.execute.return_value = result

    found_authors = await repository.get_by_ids(author_ids=[author.id])

    assert len(found_authors) == 1
    assert found_authors[0].id == author.id


@pytest.mark.asyncio
async def test_get_by_ids_returns_empty_for_empty_ids(repository: SQLAlchemyAuthorRepository) -> None:
    found_authors = await repository.get_by_ids(author_ids=[])
    assert found_authors == []


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
    session.execute.assert_awaited_once()


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

    assert len(authors) == 1
    assert authors[0].id == author.id
    assert total == 17
    session.execute.assert_awaited_once()


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


@pytest.mark.asyncio
async def test_get_by_id_returns_entity(repository: SQLAlchemyAuthorRepository, session: AsyncMock) -> None:
    author = make_author_model()
    result = Mock()
    result.scalar_one_or_none.return_value = author
    session.execute.return_value = result

    found = await repository.get_by_id(author_id=author.id)

    assert found is not None
    assert found.id == author.id


@pytest.mark.asyncio
async def test_create_persists_and_returns_author(repository: SQLAlchemyAuthorRepository, session: AsyncMock) -> None:
    data = {
        "name": "Leo Tolstoy",
        "biography": "Russian writer",
        "birthday": make_author_model().birthday,
    }

    created = await repository.create(data=data)

    assert created.name == "Leo Tolstoy"
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_returns_entity(repository: SQLAlchemyAuthorRepository, session: AsyncMock) -> None:
    updated_author = make_author_model(name="Updated")
    result = Mock()
    result.scalar_one_or_none.return_value = updated_author
    session.execute.return_value = result

    updated = await repository.update(author_id=uuid4(), data={"name": "Updated"})

    assert updated is not None
    assert updated.name == "Updated"
