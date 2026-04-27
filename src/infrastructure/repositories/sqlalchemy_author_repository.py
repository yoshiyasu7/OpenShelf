from typing import TYPE_CHECKING, Any, override

from sqlalchemy import delete, func, select, update

from src.domain.repositories.author.main import AuthorRepository
from src.infrastructure.database.models import AuthorModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemyAuthorRepository(AuthorRepository):
    """SQLAlchemy repository for author reads."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def get_by_id(self, *, author_id: UUID) -> AuthorModel | None:
        stmt = select(AuthorModel).where(AuthorModel.id == author_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def get_by_ids(self, *, author_ids: list[UUID]) -> list[AuthorModel]:
        if not author_ids:
            return []

        stmt = select(AuthorModel).where(AuthorModel.id.in_(author_ids))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @override
    async def exists_by_name(self, *, name: str, exclude_author_id: UUID | None = None) -> bool:
        normalized_name = name.strip()
        stmt = select(AuthorModel.id).where(func.lower(AuthorModel.name) == normalized_name.lower())
        if exclude_author_id is not None:
            stmt = stmt.where(AuthorModel.id != exclude_author_id)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def create(self, *, data: dict[str, Any]) -> AuthorModel:
        author = AuthorModel(**data)
        self._session.add(author)
        await self._session.flush()
        return author

    @override
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[AuthorModel], int]:
        stmt = (
            select(AuthorModel, func.count().over().label("total_count"))
            .order_by(AuthorModel.name.asc(), AuthorModel.id.asc())
            .limit(limit)
            .offset(offset)
        )

        if name_query:
            normalized_query = name_query.strip()
            stmt = stmt.where(AuthorModel.name.ilike(f"%{normalized_query}%"))

        result = await self._session.execute(stmt)
        rows = result.all()
        if not rows:
            return [], 0

        authors = [row[0] for row in rows]
        total_count = int(rows[0][1])
        return authors, total_count

    @override
    async def update(self, *, author_id: UUID, data: dict[str, Any]) -> AuthorModel | None:
        stmt = (
            update(AuthorModel)
            .where(AuthorModel.id == author_id)
            .values(**data)
            .returning(AuthorModel)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    @override
    async def delete(self, *, author_id: UUID) -> bool:
        stmt = delete(AuthorModel).where(AuthorModel.id == author_id).returning(AuthorModel.id)
        result = await self._session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None
