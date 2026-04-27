from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from src.dependencies.database import get_db_provider, get_db_session, get_transactional_session


class DummyProvider:
    def __init__(self, session: AsyncMock) -> None:
        self._session = session

    @asynccontextmanager
    async def get_session(self):
        yield self._session


def test_get_db_provider_returns_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = object()
    monkeypatch.setattr("src.dependencies.database.get_db_manager", lambda: manager)

    assert get_db_provider() is manager


@pytest.mark.asyncio
async def test_get_db_session_yields_session() -> None:
    session = AsyncMock()
    provider = DummyProvider(session)
    generator = get_db_session(provider=provider)

    yielded = await anext(generator)
    assert yielded is session


@pytest.mark.asyncio
async def test_get_transactional_session_commits_on_success() -> None:
    session = AsyncMock()
    provider = DummyProvider(session)
    generator = get_transactional_session(provider=provider)

    yielded = await anext(generator)
    assert yielded is session

    with pytest.raises(StopAsyncIteration):
        await anext(generator)

    session.commit.assert_awaited_once()
    session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_get_transactional_session_rolls_back_on_error() -> None:
    session = AsyncMock()
    provider = DummyProvider(session)
    generator = get_transactional_session(provider=provider)
    await anext(generator)

    with pytest.raises(RuntimeError):
        await generator.athrow(RuntimeError("boom"))

    session.rollback.assert_awaited_once()
