from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from src.application.use_cases.auth_use_cases import AuthUseCases, ValidateAccessTokenUseCase
from src.domain.exceptions.user import InvalidCredentialsError, UserAlreadyExistsError, UserNotFoundError
from src.infrastructure.services.jwt import TokenDecodeError, TokenValidationError


@pytest.fixture
def user_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def jwt_service() -> Mock:
    return Mock()


@pytest.fixture
def refresh_store() -> Mock:
    store = Mock()
    store.create = AsyncMock()
    store.is_active = AsyncMock()
    store.revoke = AsyncMock()
    store.rotate = AsyncMock()
    store.hash_token = Mock(return_value="hashed")
    return store


@pytest.fixture
def use_cases(user_repo: AsyncMock, jwt_service: Mock, refresh_store: Mock) -> AuthUseCases:
    uc = AuthUseCases(
        user_repository=user_repo,
        jwt=jwt_service,
        refresh_store=refresh_store,
    )
    uc._hasher = Mock()
    uc._hasher.hash.return_value = "hashed-password"
    return uc


@pytest.mark.asyncio
async def test_register_raises_when_user_already_exists(use_cases: AuthUseCases, user_repo: AsyncMock) -> None:
    user_repo.exists_by_username_or_email.return_value = True

    with pytest.raises(UserAlreadyExistsError):
        await use_cases.register(username="john", email="john@example.com", password="secret123")

    user_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_register_creates_user_with_hashed_password(use_cases: AuthUseCases, user_repo: AsyncMock) -> None:
    created_user = SimpleNamespace(id=uuid4())
    user_repo.exists_by_username_or_email.return_value = False
    user_repo.create.return_value = created_user

    result = await use_cases.register(username="john", email=None, password="secret123")

    assert result is created_user
    use_cases._hasher.hash.assert_called_once_with("secret123")
    user_repo.create.assert_awaited_once_with(
        username="john",
        email=None,
        password_hash="hashed-password",
        is_admin=False,
    )


@pytest.mark.asyncio
async def test_login_raises_on_unknown_identifier(use_cases: AuthUseCases, user_repo: AsyncMock) -> None:
    user_repo.get_by_identifier.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await use_cases.login(identifier="unknown", password="secret123")


@pytest.mark.asyncio
async def test_login_raises_on_invalid_password(use_cases: AuthUseCases, user_repo: AsyncMock) -> None:
    user_repo.get_by_identifier.return_value = SimpleNamespace(id=uuid4(), password_hash="stored")
    use_cases._hasher.verify.return_value = False

    with pytest.raises(InvalidCredentialsError):
        await use_cases.login(identifier="john", password="bad-pass")


@pytest.mark.asyncio
async def test_login_creates_refresh_session_and_returns_tokens(
    use_cases: AuthUseCases,
    user_repo: AsyncMock,
    jwt_service: Mock,
    refresh_store: Mock,
) -> None:
    user_id = uuid4()
    user = SimpleNamespace(id=user_id, password_hash="stored")
    user_repo.get_by_identifier.return_value = user
    use_cases._hasher.verify.return_value = True
    jwt_service.create_access_token.return_value = "access"
    jwt_service.create_refresh_token.return_value = "refresh"
    jwt_service.settings.refresh_token_expire_days = 7

    result = await use_cases.login(identifier="john", password="secret123")

    assert result.user is user
    assert result.tokens.access_token == "access"
    assert result.tokens.refresh_token == "refresh"
    refresh_store.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_logout_is_idempotent_for_invalid_refresh_token(
    use_cases: AuthUseCases,
    jwt_service: Mock,
    refresh_store: Mock,
) -> None:
    jwt_service.verify_refresh_token.side_effect = TokenDecodeError("broken")

    await use_cases.logout(refresh_token="bad-token")

    refresh_store.revoke.assert_not_called()


@pytest.mark.asyncio
async def test_logout_revokes_valid_refresh_token(
    use_cases: AuthUseCases,
    jwt_service: Mock,
    refresh_store: Mock,
) -> None:
    jwt_service.verify_refresh_token.return_value = SimpleNamespace(sub=uuid4())

    await use_cases.logout(refresh_token="valid-token")

    refresh_store.revoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_raises_for_invalid_refresh_token(use_cases: AuthUseCases, jwt_service: Mock) -> None:
    jwt_service.verify_refresh_token.side_effect = TokenValidationError("bad")

    with pytest.raises(InvalidCredentialsError):
        await use_cases.refresh(refresh_token="bad-token")


@pytest.mark.asyncio
async def test_refresh_raises_when_session_not_active(
    use_cases: AuthUseCases,
    jwt_service: Mock,
    refresh_store: Mock,
) -> None:
    user_id = uuid4()
    jwt_service.verify_refresh_token.return_value = SimpleNamespace(sub=user_id)
    refresh_store.hash_token.return_value = "old-hash"
    refresh_store.is_active.return_value = False

    with pytest.raises(InvalidCredentialsError):
        await use_cases.refresh(refresh_token="old-token")


@pytest.mark.asyncio
async def test_refresh_raises_when_user_missing(
    use_cases: AuthUseCases,
    jwt_service: Mock,
    refresh_store: Mock,
    user_repo: AsyncMock,
) -> None:
    user_id = uuid4()
    jwt_service.verify_refresh_token.return_value = SimpleNamespace(sub=user_id)
    refresh_store.hash_token.return_value = "old-hash"
    refresh_store.is_active.return_value = True
    user_repo.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await use_cases.refresh(refresh_token="old-token")


@pytest.mark.asyncio
async def test_refresh_rotates_and_returns_new_tokens(
    use_cases: AuthUseCases,
    jwt_service: Mock,
    refresh_store: Mock,
    user_repo: AsyncMock,
) -> None:
    user_id = uuid4()
    user = SimpleNamespace(id=user_id, username="john")
    jwt_service.verify_refresh_token.return_value = SimpleNamespace(sub=user_id)
    refresh_store.hash_token.return_value = "old-hash"
    refresh_store.is_active.return_value = True
    user_repo.get_by_id.return_value = user
    jwt_service.create_access_token.return_value = "new-access"
    jwt_service.create_refresh_token.return_value = "new-refresh"
    jwt_service.settings.refresh_token_expire_days = 30

    result = await use_cases.refresh(refresh_token="old-token")

    assert result.user is user
    assert result.tokens.access_token == "new-access"
    assert result.tokens.refresh_token == "new-refresh"
    refresh_store.rotate.assert_awaited_once()


def test_refresh_expires_at_uses_jwt_settings(use_cases: AuthUseCases, jwt_service: Mock) -> None:
    jwt_service.settings.refresh_token_expire_days = 3

    expires_at = use_cases._refresh_expires_at()

    expected = datetime.now(UTC) + timedelta(days=3)
    assert abs((expires_at - expected).total_seconds()) < 2


@pytest.mark.asyncio
async def test_validate_access_token_use_case_raises_on_invalid_token(
    jwt_service: Mock,
) -> None:
    user_repo = Mock()
    uc = ValidateAccessTokenUseCase(jwt=jwt_service, user_repository=user_repo)
    jwt_service.verify_access_token.side_effect = TokenDecodeError("broken")

    with pytest.raises(InvalidCredentialsError):
        await uc.execute(access_token="invalid")


@pytest.mark.asyncio
async def test_validate_access_token_use_case_raises_when_user_missing(
    jwt_service: Mock,
    user_repo: AsyncMock,
) -> None:
    user_id = uuid4()
    uc = ValidateAccessTokenUseCase(jwt=jwt_service, user_repository=user_repo)
    jwt_service.verify_access_token.return_value = SimpleNamespace(sub=user_id)
    user_repo.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await uc.execute(access_token="valid")


@pytest.mark.asyncio
async def test_validate_access_token_use_case_returns_user(
    jwt_service: Mock,
    user_repo: AsyncMock,
) -> None:
    user_id = uuid4()
    user = SimpleNamespace(id=user_id)
    uc = ValidateAccessTokenUseCase(jwt=jwt_service, user_repository=user_repo)
    jwt_service.verify_access_token.return_value = SimpleNamespace(sub=user_id)
    user_repo.get_by_id.return_value = user

    result = await uc.execute(access_token="valid")

    assert result is user
