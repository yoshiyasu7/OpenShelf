from typing import TYPE_CHECKING, Any, NoReturn, override

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from src.domain.exceptions.author import AuthorAlreadyExistsError
from src.domain.repositories.author.main import AuthorRepository
from src.infrastructure.database.mappers import author_to_entity
from src.infrastructure.database.models import AuthorModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.domain.entities import Author


class SQLAlchemyAuthorRepository(AuthorRepository):
    """SQLAlchemy repository for author persistence.

    Returns domain entities only; ORM models never leak out of this layer.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def get_by_id(self, *, author_id: UUID) -> Author | None:
        stmt = select(AuthorModel).options(joinedload(AuthorModel.books)).where(AuthorModel.id == author_id)
        result = await self._session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        return author_to_entity(model) if model is not None else None

    @override
    async def get_by_ids(self, *, author_ids: list[UUID]) -> list[Author]:
        if not author_ids:
            return []

        stmt = select(AuthorModel).where(AuthorModel.id.in_(author_ids))
        result = await self._session.execute(stmt)
        return [author_to_entity(model, include_books=False) for model in result.scalars().all()]

    @override
    async def exists_by_name(self, *, name: str, exclude_author_id: UUID | None = None) -> bool:
        normalized_name = name.strip()
        stmt = select(AuthorModel.id).where(func.lower(AuthorModel.name) == normalized_name.lower())
        if exclude_author_id is not None:
            stmt = stmt.where(AuthorModel.id != exclude_author_id)

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def create(self, *, data: dict[str, Any]) -> Author:
        author = AuthorModel(**data)
        self._session.add(author)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            self._translate_unique_violation(exc)
        return author_to_entity(author, include_books=False)

    @override
    async def list_paginated(
        self,
        *,
        limit: int,
        offset: int,
        name_query: str | None,
    ) -> tuple[list[Author], int]:
        stmt = (
            select(AuthorModel, func.count().over().label("total_count"))
            .options(selectinload(AuthorModel.books))
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
            return [], await self._count(name_query=name_query) if offset > 0 else 0

        authors = [author_to_entity(row[0]) for row in rows]
        total_count = int(rows[0][1])
        return authors, total_count

    @override
    async def update(self, *, author_id: UUID, data: dict[str, Any]) -> Author | None:
        stmt = update(AuthorModel).where(AuthorModel.id == author_id).values(**data).returning(AuthorModel)
        try:
            result = await self._session.execute(stmt)
        except IntegrityError as exc:
            self._translate_unique_violation(exc)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return await self.get_by_id(author_id=author_id)

    @override
    async def delete(self, *, author_id: UUID) -> bool:
        stmt = delete(AuthorModel).where(AuthorModel.id == author_id).returning(AuthorModel.id)
        result = await self._session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    async def _count(self, *, name_query: str | None) -> int:
        stmt = select(func.count(AuthorModel.id))
        if name_query:
            normalized_query = name_query.strip()
            stmt = stmt.where(AuthorModel.name.ilike(f"%{normalized_query}%"))
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    @staticmethod
    def _translate_unique_violation(exc: IntegrityError) -> NoReturn:
        message = str(exc.orig).lower() if exc.orig is not None else ""
        if "ux_authors_name_lower" in message:
            raise AuthorAlreadyExistsError() from exc
        raise exc
