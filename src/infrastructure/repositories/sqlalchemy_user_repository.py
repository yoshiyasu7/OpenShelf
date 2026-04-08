from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.user.main import UserRepository
from src.infrastructure.database.models import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy repository for user reads."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, *, user_id: UUID) -> UserModel | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identifier(self, *, identifier: str) -> UserModel | None:
        stmt = select(UserModel).where(or_(UserModel.username == identifier, UserModel.email == identifier))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_username_or_email(self, *, username: str, email: str | None) -> bool:
        conditions = [UserModel.username == username]
        if email is not None:
            conditions.append(UserModel.email == email)

        stmt = select(UserModel.id).where(or_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        *,
        username: str,
        email: str | None,
        password_hash: str,
        is_admin: bool = False,
    ) -> UserModel:
        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
        )
        self._session.add(user)
        await self._session.flush()
        return user
