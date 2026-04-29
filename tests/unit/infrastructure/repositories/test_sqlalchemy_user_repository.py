from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions.user import EmailAlreadyTakenError, UsernameAlreadyTakenError
from src.infrastructure.database.models import UserModel
from src.infrastructure.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


def make_user_model(*, username: str = "john", is_admin: bool = False) -> UserModel:
    now = datetime.now(UTC)
    return UserModel(
        id=uuid4(),
        username=username,
        email=f"{username}@example.com",
        password_hash="hash",
        is_admin=is_admin,
        books_on_hand=0,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def session() -> AsyncMock:
    session_mock = AsyncMock()
    session_mock.add = Mock()
    return session_mock


@pytest.fixture
def repository(session: AsyncMock) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(session=session)


@pytest.mark.asyncio
async def test_get_by_id_returns_entity(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    user = make_user_model()
    result = Mock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    found = await repository.get_by_id(user_id=user.id)

    assert found is not None
    assert found.id == user.id
    assert found.username == user.username


@pytest.mark.asyncio
async def test_get_by_identifier_returns_entity(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    user = make_user_model()
    result = Mock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    found = await repository.get_by_identifier(identifier="john")

    assert found is not None
    assert found.username == "john"


@pytest.mark.asyncio
async def test_exists_by_username_or_email_without_email(
    repository: SQLAlchemyUserRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result

    exists = await repository.exists_by_username_or_email(username="john", email=None)

    assert exists is True


@pytest.mark.asyncio
async def test_exists_by_username_or_email_with_email(
    repository: SQLAlchemyUserRepository,
    session: AsyncMock,
) -> None:
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
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_returns_entity(repository: SQLAlchemyUserRepository, session: AsyncMock) -> None:
    user = make_user_model(username="new")
    result = Mock()
    result.scalar_one_or_none.return_value = user
    session.execute.return_value = result

    updated = await repository.update(user_id=user.id, data={"username": "new"})

    assert updated is not None
    assert updated.username == "new"


@pytest.mark.asyncio
async def test_delete_returns_false_when_not_deleted(
    repository: SQLAlchemyUserRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.fetchone.return_value = None
    session.execute.return_value = result

    deleted = await repository.delete(user_id=uuid4())

    assert deleted is False


@pytest.mark.asyncio
async def test_update_translates_username_conflict(
    repository: SQLAlchemyUserRepository,
    session: AsyncMock,
) -> None:
    err = IntegrityError("stmt", {}, Exception("users_username_key"))
    session.execute.side_effect = err

    with pytest.raises(UsernameAlreadyTakenError):
        await repository.update(user_id=uuid4(), data={"username": "john"})


@pytest.mark.asyncio
async def test_update_translates_email_conflict(
    repository: SQLAlchemyUserRepository,
    session: AsyncMock,
) -> None:
    err = IntegrityError("stmt", {}, Exception("users_email_key"))
    session.execute.side_effect = err

    with pytest.raises(EmailAlreadyTakenError):
        await repository.update(user_id=uuid4(), data={"email": "a@b.com"})


@pytest.mark.asyncio
async def test_update_propagates_unknown_integrity_error(
    repository: SQLAlchemyUserRepository,
    session: AsyncMock,
) -> None:
    err = IntegrityError("stmt", {}, Exception("other_constraint"))
    session.execute.side_effect = err

    with pytest.raises(IntegrityError):
        await repository.update(user_id=uuid4(), data={"username": "john"})
