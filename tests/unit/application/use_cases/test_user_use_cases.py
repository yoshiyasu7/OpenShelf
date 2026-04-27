from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.user.main import UpdateUserRequest
from src.application.use_cases.user_use_cases import UserUseCases
from src.domain.exceptions.user import UserNotFoundError


@pytest.fixture
def user_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_cases(user_repo: AsyncMock) -> UserUseCases:
    return UserUseCases(user_repository=user_repo)


@pytest.mark.asyncio
async def test_get_user_raises_when_missing(use_cases: UserUseCases, user_repo: AsyncMock) -> None:
    user_repo.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await use_cases.get_user(user_id=uuid4())


@pytest.mark.asyncio
async def test_get_user_returns_user(use_cases: UserUseCases, user_repo: AsyncMock) -> None:
    user = SimpleNamespace(id=uuid4())
    user_repo.get_by_id.return_value = user

    result = await use_cases.get_user(user_id=user.id)

    assert result is user


@pytest.mark.asyncio
async def test_update_user_returns_existing_when_payload_empty(use_cases: UserUseCases, user_repo: AsyncMock) -> None:
    user_id = uuid4()
    user = SimpleNamespace(id=user_id)
    user_repo.get_by_id.return_value = user

    result = await use_cases.update_user(user_id=user_id, payload=UpdateUserRequest())

    assert result is user
    user_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_user_with_empty_payload_raises_when_missing(
    use_cases: UserUseCases,
    user_repo: AsyncMock,
) -> None:
    user_repo.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await use_cases.update_user(user_id=uuid4(), payload=UpdateUserRequest())


@pytest.mark.asyncio
async def test_update_user_raises_when_user_missing_on_update(
    use_cases: UserUseCases,
    user_repo: AsyncMock,
) -> None:
    user_repo.update.return_value = None

    with pytest.raises(UserNotFoundError):
        await use_cases.update_user(user_id=uuid4(), payload=UpdateUserRequest(username="new-name"))


@pytest.mark.asyncio
async def test_update_user_returns_updated_user(use_cases: UserUseCases, user_repo: AsyncMock) -> None:
    user = SimpleNamespace(id=uuid4(), username="new-name")
    user_repo.update.return_value = user

    result = await use_cases.update_user(user_id=user.id, payload=UpdateUserRequest(username="new-name"))

    assert result is user


@pytest.mark.asyncio
async def test_delete_user_raises_when_missing(use_cases: UserUseCases, user_repo: AsyncMock) -> None:
    user_repo.delete.return_value = False

    with pytest.raises(UserNotFoundError):
        await use_cases.delete_user(user_id=uuid4())
