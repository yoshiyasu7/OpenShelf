from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

from src.infrastructure.database.database_manager import DatabaseManager, _json_serializer


def test_json_serializer_preserves_unicode() -> None:
    payload = {"text": "Привет"}
    serialized = _json_serializer(payload)
    assert "Привет" in serialized


@pytest.mark.asyncio
async def test_initialize_sets_engine_and_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db", debug=True)
    engine = Mock()
    session_factory = Mock()
    create_engine_mock = Mock(return_value=engine)
    sessionmaker_mock = Mock(return_value=session_factory)
    monkeypatch.setattr("src.infrastructure.database.database_manager.create_async_engine", create_engine_mock)
    monkeypatch.setattr("src.infrastructure.database.database_manager.async_sessionmaker", sessionmaker_mock)

    await manager.initialize()

    assert manager._engine is engine
    assert manager._session_factory is session_factory


@pytest.mark.asyncio
async def test_initialize_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
    manager._engine = Mock()
    create_engine_mock = Mock()
    monkeypatch.setattr("src.infrastructure.database.database_manager.create_async_engine", create_engine_mock)

    await manager.initialize()

    create_engine_mock.assert_not_called()


@pytest.mark.asyncio
async def test_shutdown_disposes_engine() -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
    engine = AsyncMock()
    manager._engine = engine
    manager._session_factory = Mock()

    await manager.shutdown()

    engine.dispose.assert_awaited_once()
    assert manager._engine is None
    assert manager._session_factory is None


@pytest.mark.asyncio
async def test_shutdown_without_engine_is_noop() -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")

    await manager.shutdown()


@pytest.mark.asyncio
async def test_get_session_raises_without_initialization() -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")

    with pytest.raises(RuntimeError):
        async with manager.get_session():
            pass


@pytest.mark.asyncio
async def test_get_session_yields_session() -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
    session = AsyncMock()

    @asynccontextmanager
    async def fake_session_cm():
        yield session

    manager._session_factory = fake_session_cm

    async with manager.get_session() as got:
        assert got is session


@pytest.mark.asyncio
async def test_health_check_with_engine_and_without_engine() -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
    assert await manager.health_check() == {"status": "down", "available": False}

    pool = Mock()
    pool.size.return_value = 1
    pool.checkedin.return_value = 2
    pool.checkedout.return_value = 3
    pool.overflow.return_value = 4
    pool.invalid.return_value = 5
    manager._engine = Mock(pool=pool)
    session = AsyncMock()

    @asynccontextmanager
    async def fake_session_cm():
        yield session

    manager._session_factory = fake_session_cm
    health = await manager.health_check()

    assert health == {
        "status": "up",
        "available": True,
        "pool_size": 1,
        "checked_in": 2,
        "checked_out": 3,
        "overflow": 4,
        "invalid": 5,
    }


def test_repr_contains_database_url() -> None:
    manager = DatabaseManager("postgresql+asyncpg://user:pass@localhost/db")
    assert "postgresql+asyncpg://user:pass@localhost/db" in repr(manager)
