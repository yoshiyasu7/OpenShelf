from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.infrastructure.auth.refresh_sessions import RefreshSessionStore


@pytest.fixture
def repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def store(repository: AsyncMock) -> RefreshSessionStore:
    return RefreshSessionStore(repository=repository)


def test_hash_token_is_stable() -> None:
    token = "refresh-token"

    first = RefreshSessionStore.hash_token(token)
    second = RefreshSessionStore.hash_token(token)

    assert first == second
    assert len(first) == 64


@pytest.mark.asyncio
async def test_create_hashes_token_before_store(store: RefreshSessionStore, repository: AsyncMock) -> None:
    user_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=10)

    await store.create(user_id=user_id, refresh_token="plain-token", expires_at=expires_at)

    repository.create.assert_awaited_once()
    token_hash = repository.create.call_args.kwargs["token_hash"]
    assert token_hash != "plain-token"


@pytest.mark.asyncio
async def test_revoke_hashes_token(store: RefreshSessionStore, repository: AsyncMock) -> None:
    now = datetime.now(UTC)
    await store.revoke(refresh_token="plain-token", now=now)

    repository.revoke.assert_awaited_once()
    token_hash = repository.revoke.call_args.kwargs["token_hash"]
    assert token_hash != "plain-token"


@pytest.mark.asyncio
async def test_rotate_raises_when_old_token_not_active(store: RefreshSessionStore, repository: AsyncMock) -> None:
    repository.revoke_for_user.return_value = False

    with pytest.raises(ValueError):
        await store.rotate(
            user_id=uuid4(),
            old_refresh_token="old",
            new_refresh_token="new",
            new_expires_at=datetime.now(UTC) + timedelta(days=1),
            now=datetime.now(UTC),
        )


@pytest.mark.asyncio
async def test_rotate_raises_when_revoke_not_updated(store: RefreshSessionStore, repository: AsyncMock) -> None:
    repository.revoke_for_user.return_value = False

    with pytest.raises(ValueError):
        await store.rotate(
            user_id=uuid4(),
            old_refresh_token="old",
            new_refresh_token="new",
            new_expires_at=datetime.now(UTC) + timedelta(days=1),
            now=datetime.now(UTC),
        )


@pytest.mark.asyncio
async def test_rotate_revokes_old_and_creates_new(store: RefreshSessionStore, repository: AsyncMock) -> None:
    repository.revoke_for_user.return_value = True
    expires = datetime.now(UTC) + timedelta(days=1)
    user_id = uuid4()

    await store.rotate(
        user_id=user_id,
        old_refresh_token="old",
        new_refresh_token="new",
        new_expires_at=expires,
        now=datetime.now(UTC),
    )

    repository.revoke_for_user.assert_awaited_once()
    repository.create.assert_awaited_once()
