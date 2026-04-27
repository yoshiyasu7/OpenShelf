from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
import pytest

from src.dependencies.auth import get_current_admin, get_current_user
from src.domain.exceptions.user import InvalidCredentialsError


@pytest.mark.asyncio
async def test_get_current_user_raises_when_no_credentials() -> None:
    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=None, uc=AsyncMock())

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_raises_on_invalid_scheme() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Basic", credentials="token")

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=credentials, uc=AsyncMock())

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_raises_on_invalid_token() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    validate_uc = AsyncMock()
    validate_uc.execute.side_effect = InvalidCredentialsError()

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials=credentials, uc=validate_uc)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_user_returns_user(monkeypatch: pytest.MonkeyPatch) -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    user = SimpleNamespace(id=uuid4(), username="john", email="john@example.com", is_admin=False)
    validate_uc = AsyncMock()
    validate_uc.execute.return_value = user
    bound: dict[str, str] = {}

    def fake_bind_contextvars(**kwargs: str) -> None:
        bound.update(kwargs)

    monkeypatch.setattr("src.dependencies.auth.structlog.contextvars.bind_contextvars", fake_bind_contextvars)

    current_user = await get_current_user(credentials=credentials, uc=validate_uc)

    assert current_user.id == user.id
    assert bound["user_id"] == str(user.id)


@pytest.mark.asyncio
async def test_get_current_admin_raises_for_non_admin() -> None:
    current_user = SimpleNamespace(is_admin=False)

    with pytest.raises(HTTPException) as exc:
        await get_current_admin(current_user=current_user)

    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_get_current_admin_returns_admin_user() -> None:
    current_user = SimpleNamespace(is_admin=True)

    result = await get_current_admin(current_user=current_user)

    assert result is current_user
