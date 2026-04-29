import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from src.domain.repositories.session.main import SessionRepository


class RefreshSessionStore:
    """
    Refresh session persistence helpers (adapter for RefreshSessionStore port).

    Stores only SHA-256 hashes of refresh token strings.
    """

    def __init__(self, repository: SessionRepository) -> None:
        self._repository = repository

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def create(
        self,
        *,
        user_id: UUID,
        refresh_token: str,
        expires_at: datetime,
    ) -> None:
        await self._repository.create(
            user_id=user_id,
            token_hash=self.hash_token(refresh_token),
            expires_at=expires_at,
        )

    async def revoke(self, *, refresh_token: str, now: datetime) -> None:
        token_hash = self.hash_token(refresh_token)
        await self._repository.revoke(token_hash=token_hash, now=now)

    async def rotate(
        self,
        *,
        user_id: UUID,
        old_refresh_token: str,
        new_refresh_token: str,
        new_expires_at: datetime,
        now: datetime,
    ) -> None:
        """
        Rotation with single-transaction semantics (caller should use transactional session).

        - old token must be active (not revoked, not expired)
        - old token is revoked and linked to new token hash
        - new token hash is inserted
        """
        old_hash = self.hash_token(old_refresh_token)

        updated = await self._repository.revoke_for_user(
            user_id=user_id,
            token_hash=old_hash,
            now=now,
        )
        if not updated:
            raise ValueError("Refresh token is not active.")

        await self.create(user_id=user_id, refresh_token=new_refresh_token, expires_at=new_expires_at)
