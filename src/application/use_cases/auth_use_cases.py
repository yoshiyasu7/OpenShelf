from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from src.application.ports import (
    TokenDecodeError,
    TokenValidationError,
)
from src.domain.exceptions.user import InvalidCredentialsError, UserAlreadyExistsError, UserNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.ports import PasswordHasher, RefreshSessionStore, TokenService
    from src.domain.entities import User
    from src.domain.repositories.user.main import UserRepository


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class AuthResult:
    user: User
    tokens: AuthTokens


class AuthUseCases:
    """
    Application-level auth logic (register/login/logout/refresh).

    Notes:
    - access token is stateless JWT
    - refresh token is JWT + server-side session row (hashed) for revocation/rotation
    - all external dependencies are supplied through ports (no infra imports)
    """

    def __init__(
        self,
        *,
        user_repository: UserRepository,
        token_service: TokenService,
        refresh_store: RefreshSessionStore,
        password_hasher: PasswordHasher,
        refresh_token_expire_days: int,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service
        self._refresh_store = refresh_store
        self._hasher = password_hasher
        self._refresh_token_expire_days = refresh_token_expire_days

    async def register(self, *, username: str, email: str | None, password: str) -> User:
        if await self._user_repository.exists_by_username_or_email(username=username, email=email):
            raise UserAlreadyExistsError("User already exists.")

        return await self._user_repository.create(
            username=username,
            email=email,
            password_hash=self._hasher.hash(password),
            is_admin=False,
        )

    async def login(self, *, identifier: str, password: str) -> AuthResult:
        user = await self._user_repository.get_by_identifier(identifier=identifier)
        if user is None:
            raise InvalidCredentialsError("Invalid credentials.")

        if not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials.")

        tokens = self._issue_tokens(user_id=user.id)
        await self._refresh_store.create(
            user_id=user.id,
            refresh_token=tokens.refresh_token,
            expires_at=self._refresh_expires_at(),
        )
        return AuthResult(user, tokens)

    async def logout(self, *, refresh_token: str) -> None:
        try:
            self._token_service.verify_refresh_token(refresh_token)
        except (TokenDecodeError, TokenValidationError):
            # Idempotent: invalid/expired token -> no-op.
            return

        await self._refresh_store.revoke(refresh_token=refresh_token, now=datetime.now(UTC))

    async def refresh(self, *, refresh_token: str) -> AuthResult:
        now = datetime.now(UTC)
        try:
            payload = self._token_service.verify_refresh_token(refresh_token)
        except (TokenDecodeError, TokenValidationError) as exc:
            raise InvalidCredentialsError("Invalid refresh token.") from exc

        user_id = payload.sub
        user = await self._user_repository.get_by_id(user_id=user_id)
        if user is None:
            raise InvalidCredentialsError("Invalid refresh token.")

        new_tokens = self._issue_tokens(user_id=user_id)
        try:
            await self._refresh_store.rotate(
                user_id=user_id,
                old_refresh_token=refresh_token,
                new_refresh_token=new_tokens.refresh_token,
                new_expires_at=self._refresh_expires_at(),
                now=now,
            )
        except ValueError as exc:
            raise InvalidCredentialsError("Refresh token is not active.") from exc
        return AuthResult(user, new_tokens)

    def _issue_tokens(self, *, user_id: UUID) -> AuthTokens:
        return AuthTokens(
            access_token=self._token_service.create_access_token(user_id),
            refresh_token=self._token_service.create_refresh_token(user_id),
        )

    def _refresh_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(days=self._refresh_token_expire_days)


class ValidateAccessTokenUseCase:
    """Validate access token and load current user."""

    def __init__(
        self,
        *,
        token_service: TokenService,
        user_repository: UserRepository,
    ) -> None:
        self._token_service = token_service
        self._user_repository = user_repository

    async def execute(self, *, access_token: str) -> User:
        try:
            payload = self._token_service.verify_access_token(access_token)
        except (TokenDecodeError, TokenValidationError) as exc:
            raise InvalidCredentialsError("Invalid access token.") from exc

        user = await self._user_repository.get_by_id(user_id=payload.sub)
        if user is None:
            raise UserNotFoundError(f"User with id {payload.sub} not found")

        return user
