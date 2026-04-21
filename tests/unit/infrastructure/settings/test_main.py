import pytest

from src.infrastructure.settings.main import JWTSettings, _get_required_env, get_settings


def test_get_required_env_raises_for_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_VAR", raising=False)

    with pytest.raises(RuntimeError):
        _get_required_env("MISSING_VAR")


def test_get_settings_reads_env_and_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    monkeypatch.setenv("DB_URL", "postgresql+asyncpg://user:pass@localhost/db")
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
    assert isinstance(first.jwt, JWTSettings)
