import pytest
from types import SimpleNamespace

from src.infrastructure.database.provider import get_db_manager, init_db_manager


def test_get_db_manager_raises_before_init(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.infrastructure.database.provider._db_manager", None)

    with pytest.raises(RuntimeError):
        get_db_manager()


def test_init_db_manager_creates_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.infrastructure.database.provider._db_manager", None)
    settings = SimpleNamespace(
        db=SimpleNamespace(
            debug=False,
            url="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=1,
            max_overflow=2,
            pool_recycle=100,
        )
    )

    manager = init_db_manager(settings)

    assert manager.database_url == settings.db.url
    assert get_db_manager() is manager
