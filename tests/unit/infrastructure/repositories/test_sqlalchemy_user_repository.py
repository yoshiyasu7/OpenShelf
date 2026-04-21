from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


@pytest.fixture
def session() -> AsyncMock:
    session_mock = AsyncMock()
    session_mock.add = Mock()
    return session_mock


@pytest.fixture
def repository(session: AsyncMock) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session=session)


@pytest.mark.asyncio
async def test_get_by_id_returns_model(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    user = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    found = await repository.get_by_id(user_id=uuid4())

    assert found is user


@pytest.mark.asyncio
async def test_get_by_identifier_returns_model(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    user = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    found = await repository.get_by_identifier(identifier="john")

    assert found is user


@pytest.mark.asyncio
async def test_exists_by_username_or_email_without_email(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result

    exists = await repository.exists_by_username_or_email(username="john", email=None)

    assert exists is True


@pytest.mark.asyncio
async def test_exists_by_username_or_email_with_email(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    exists = await repository.exists_by_username_or_email(username="john", email="john@example.com")

    assert exists is False


@pytest.mark.asyncio
async def test_create_adds_and_flushes(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    created = await repository.create(
        username="john",
        email="john@example.com",
        password_hash="hash",
        is_admin=True,
    )

    assert created.username == "john"
    assert created.is_admin is True
    session.add.assert_called_once_with(created)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_returns_model(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    user = Mock()
    result = Mock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    updated = await repository.update(user_id=uuid4(), data={"username": "new"})

    assert updated is user


@pytest.mark.asyncio
async def test_delete_returns_false_when_not_deleted(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    result = Mock()
    result.fetchone.return_value = None
    session.execute.return_value = result

    deleted = await repository.delete(user_id=uuid4())

    assert deleted is False
