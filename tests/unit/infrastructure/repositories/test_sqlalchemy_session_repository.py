from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.infrastructure.repositories.sqlalchemy_session_repository import SQLAlchemySessionRepository


@pytest.fixture
def session() -> AsyncMock:
    session_mock = AsyncMock()
    session_mock.add = Mock()
    return session_mock


@pytest.fixture
def repository(session: AsyncMock) -> SQLAlchemySessionRepository:
    return SQLAlchemySessionRepository(session=session)


@pytest.mark.asyncio
async def test_create_adds_and_flushes(repository: SQLAlchemySessionRepository, session: AsyncMock) -> None:
    now = datetime.now(UTC)
    model = await repository.create(user_id=uuid4(), token_hash="hash", expires_at=now + timedelta(days=1))

    assert model.token_hash == "hash"
    session.add.assert_called_once_with(model)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_active_returns_boolean(repository: SQLAlchemySessionRepository, session: AsyncMock) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result

    is_active = await repository.is_active(token_hash="hash", now=datetime.now(UTC))

    assert is_active is True


@pytest.mark.asyncio
async def test_revoke_executes_update(repository: SQLAlchemySessionRepository, session: AsyncMock) -> None:
    await repository.revoke(token_hash="hash", now=datetime.now(UTC))

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_revoke_for_user_uses_execute_result(repository: SQLAlchemySessionRepository, session: AsyncMock) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = uuid4()
    session.execute.return_value = result

    revoked = await repository.revoke_for_user(user_id=uuid4(), token_hash="hash", now=datetime.now(UTC))

    assert revoked is True


@pytest.mark.asyncio
async def test_revoke_for_user_returns_false_when_not_updated(
    repository: SQLAlchemySessionRepository,
    session: AsyncMock,
) -> None:
    result = Mock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    revoked = await repository.revoke_for_user(user_id=uuid4(), token_hash="hash", now=datetime.now(UTC))

    assert revoked is False
