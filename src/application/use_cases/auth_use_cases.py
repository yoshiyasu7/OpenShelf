from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from src.domain.exceptions.user import InvalidCredentialsError, UserAlreadyExistsError, UserNotFoundError
from src.infrastructure.auth.passwords import PasswordHasher
from src.infrastructure.services.jwt import JWTService, TokenDecodeError, TokenValidationError

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.repositories.user.main import UserRepository
    from src.infrastructure.auth.refresh_sessions import RefreshSessionStore
    from src.infrastructure.database.models import UserModel


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class AuthResult:
    user: UserModel
    tokens: AuthTokens


class AuthUseCases:
    """
    Application-level auth logic (register/login/logout/refresh).

    Notes:
    - access token is stateless JWT
    - refresh token is JWT + server-side session row (hashed) for revocation/rotation
    """

    def __init__(
        self,
        *,
        user_repository: UserRepository,
        jwt: JWTService,
        refresh_store: RefreshSessionStore,
    ) -> None:
        self._user_repository = user_repository
        self._jwt = jwt
        self._refresh_store = refresh_store
        self._hasher = PasswordHasher()

    async def register(self, *, username: str, email: str | None, password: str) -> UserModel:
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
        return AuthResult(user=user, tokens=tokens)

    async def logout(self, *, refresh_token: str) -> None:
        # Idempotent: even if token invalid/unknown -> no error.
        now = datetime.now(UTC)
        try:
            self._jwt.verify_refresh_token(refresh_token)
        except (TokenDecodeError, TokenValidationError):
            return

        await self._refresh_store.revoke(refresh_token=refresh_token, now=now)

    async def refresh(self, *, refresh_token: str) -> AuthResult:
        now = datetime.now(UTC)
        try:
            payload = self._jwt.verify_refresh_token(refresh_token)
        except (TokenDecodeError, TokenValidationError) as exc:
            raise InvalidCredentialsError("Invalid refresh token.") from exc

        user_id: UUID = payload.sub
        old_hash = self._refresh_store.hash_token(refresh_token)
        if not await self._refresh_store.is_active(token_hash=old_hash, now=now):
            raise InvalidCredentialsError("Invalid refresh token.")

        user = await self._user_repository.get_by_id(user_id=user_id)
        if user is None:
            raise UserNotFoundError("User not found.")

        new_tokens = self._issue_tokens(user_id=user_id)
        await self._refresh_store.rotate(
            user_id=user_id,
            old_refresh_token=refresh_token,
            new_refresh_token=new_tokens.refresh_token,
            new_expires_at=self._refresh_expires_at(),
            now=now,
        )
        return AuthResult(user=user, tokens=new_tokens)

    def _issue_tokens(self, *, user_id: UUID) -> AuthTokens:
        return AuthTokens(
            access_token=self._jwt.create_access_token(user_id),
            refresh_token=self._jwt.create_refresh_token(user_id),
        )

    def _refresh_expires_at(self) -> datetime:
        days = self._jwt.settings.refresh_token_expire_days
        return datetime.now(UTC) + timedelta(days=days)


class ValidateAccessTokenUseCase:
    """Validate access token and load current user."""

    def __init__(self, *, jwt: JWTService, user_repository: UserRepository) -> None:
        self._jwt = jwt
        self._user_repository = user_repository

    async def execute(self, *, access_token: str) -> UserModel:
        try:
            payload = self._jwt.verify_access_token(access_token)
        except (TokenDecodeError, TokenValidationError) as exc:
            raise InvalidCredentialsError("Invalid access token.") from exc

        user = await self._user_repository.get_by_id(user_id=payload.sub)
        if user is None:
            raise UserNotFoundError("User not found.")

        return user
