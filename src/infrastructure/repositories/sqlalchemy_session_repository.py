from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models import RefreshSessionModel


class SQLAlchemySessionRepository:
    """SQLAlchemy repository for refresh session persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshSessionModel:
        model = RefreshSessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._session.add(model)
        await self._session.flush()
        return model

    async def is_active(self, *, token_hash: str, now: datetime) -> bool:
        stmt = select(RefreshSessionModel.id).where(
            RefreshSessionModel.token_hash == token_hash,
            RefreshSessionModel.revoked_at.is_(None),
            RefreshSessionModel.expires_at > now,
        )
        res = await self._session.execute(stmt)
        return res.scalar_one_or_none() is not None

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

    async def revoke_for_user(self, *, user_id: UUID, token_hash: str, now: datetime) -> bool:
        stmt = (
            update(RefreshSessionModel)
            .where(
                RefreshSessionModel.token_hash == token_hash,
                RefreshSessionModel.user_id == user_id,
                RefreshSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
