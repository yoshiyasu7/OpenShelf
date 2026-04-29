from typing import TYPE_CHECKING, override

from sqlalchemy import update

from src.domain.repositories.session.main import SessionRepository
from src.infrastructure.database.models import RefreshSessionModel

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemySessionRepository(SessionRepository):
    """SQLAlchemy repository for refresh session persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        model = RefreshSessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()

    @override
    async def revoke(self, *, token_hash: str, now: datetime) -> None:
        stmt = (
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.token_hash == token_hash,
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await self._session.execute(stmt)

    @override
    async def revoke_for_user(self, *, user_id: UUID, token_hash: str, now: datetime) -> bool:
        stmt = (
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.token_hash == token_hash,
                RefreshSessionModel.user_id == user_id,
                RefreshSessionModel.revoked_at.is_(None),
                RefreshSessionModel.expires_at > now,
            )
            .values(revoked_at=now)
            .returning(RefreshSessionModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
