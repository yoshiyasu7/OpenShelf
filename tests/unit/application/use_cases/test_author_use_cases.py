from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.author.main import CreateAuthorRequest, UpdateAuthorRequest
from src.application.dtos.main import QueryFilterParams
from src.application.use_cases.author_use_cases import AuthorUseCases
from src.domain.exceptions.author import AuthorAlreadyExistsError, AuthorNotFoundError
from src.domain.repositories.author.main import AuthorRepository
from tests.helpers import make_author_model


@pytest.fixture
def author_repo() -> AsyncMock:
    return AsyncMock(spec=AuthorRepository)


@pytest.fixture
def use_cases(author_repo: AsyncMock) -> AuthorUseCases:
    return AuthorUseCases(author_repository=author_repo)


@pytest.mark.asyncio
async def test_create_author_raises_when_name_exists(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    payload = CreateAuthorRequest(
        name="Leo Tolstoy",
        biography="Russian writer",
        birthday="1828-09-09",
    )
    author_repo.exists_by_name.return_value = True

    with pytest.raises(AuthorAlreadyExistsError):
        await use_cases.create_author(payload=payload)

    author_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_create_author_creates_entity(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    payload = CreateAuthorRequest(
        name="Leo Tolstoy",
        biography="Russian writer",
        birthday="1828-09-09",
    )
    created_author = make_author_model()
    author_repo.exists_by_name.return_value = False
    author_repo.create.return_value = created_author

    author = await use_cases.create_author(payload=payload)

    assert author == created_author
    author_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_author_raises_when_missing(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    author_id = uuid4()
    author_repo.get_by_id.return_value = None

    with pytest.raises(AuthorNotFoundError):
        await use_cases.get_author(author_id=author_id)


@pytest.mark.asyncio
async def test_get_authors_list_returns_paginated_payload(
    use_cases: AuthorUseCases,
    author_repo: AsyncMock,
) -> None:
    filters = QueryFilterParams(limit=5, offset=10, name_query="tol")
    authors = [make_author_model()]
    author_repo.list_paginated.return_value = (authors, 24)

    result = await use_cases.get_authors_list(filters=filters)

    assert result.items == authors
    assert result.total == 24
    assert result.limit == 5
    assert result.offset == 10


@pytest.mark.asyncio
async def test_update_author_with_empty_payload_returns_existing(
    use_cases: AuthorUseCases,
    author_repo: AsyncMock,
) -> None:
    author_id = uuid4()
    existing = make_author_model(author_id=author_id)
    payload = UpdateAuthorRequest()
    author_repo.get_by_id.return_value = existing

    updated = await use_cases.update_author(author_id=author_id, payload=payload)

    assert updated == existing
    author_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_author_raises_when_name_conflicts(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    author_id = uuid4()
    payload = UpdateAuthorRequest(name="Leo Tolstoy")
    author_repo.exists_by_name.return_value = True

    with pytest.raises(AuthorAlreadyExistsError):
        await use_cases.update_author(author_id=author_id, payload=payload)

    author_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_author_raises_when_entity_missing(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    author_id = uuid4()
    payload = UpdateAuthorRequest(name="New Name")
    author_repo.exists_by_name.return_value = False
    author_repo.update.return_value = None

    with pytest.raises(AuthorNotFoundError):
        await use_cases.update_author(author_id=author_id, payload=payload)


@pytest.mark.asyncio
async def test_delete_author_raises_when_entity_missing(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    author_id = uuid4()
    author_repo.delete.return_value = False

    with pytest.raises(AuthorNotFoundError):
        await use_cases.delete_author(author_id=author_id)


@pytest.mark.asyncio
async def test_update_author_returns_updated_entity(use_cases: AuthorUseCases, author_repo: AsyncMock) -> None:
    author_id = uuid4()
    payload = UpdateAuthorRequest(name="Lev Tolstoy")
    updated = make_author_model(author_id=author_id, name="Lev Tolstoy")
    author_repo.exists_by_name.return_value = False
    author_repo.update.return_value = updated

    result = await use_cases.update_author(author_id=author_id, payload=payload)

    assert result == updated
