from typing import TYPE_CHECKING, Any, NoReturn, override

from sqlalchemy import delete, or_, select, update
from sqlalchemy.exc import IntegrityError

from src.domain.exceptions.user import (
    EmailAlreadyTakenError,
    UsernameAlreadyTakenError,
)
from src.domain.repositories.user.main import UserRepository
from src.infrastructure.database.mappers import user_to_entity
from src.infrastructure.database.models import UserModel

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.domain.entities import User


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy repository for user persistence.

    Returns domain entities only; ORM models never leak out of this layer.
    Translates known IntegrityError constraints into domain conflicts.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def get_by_id(self, *, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    @override
    async def get_by_identifier(self, *, identifier: str) -> User | None:
        stmt = select(UserModel).where(or_(UserModel.username == identifier, UserModel.email == identifier))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    @override
    async def exists_by_username_or_email(self, *, username: str, email: str | None) -> bool:
        conditions = [UserModel.username == username]
        if email is not None:
            conditions.append(UserModel.email == email)

        stmt = select(UserModel.id).where(or_(*conditions))
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    @override
    async def create(
        self,
        *,
        username: str,
        email: str | None,
        password_hash: str,
        is_admin: bool = False,
    ) -> User:
        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_admin,
        )
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            self._translate_unique_violation(exc)
        return user_to_entity(user)

    @override
    async def update(self, *, user_id: UUID, data: dict[str, Any]) -> User | None:
        stmt = update(UserModel).where(UserModel.id == user_id).values(**data).returning(UserModel)
        try:
            result = await self._session.execute(stmt)
        except IntegrityError as exc:
            self._translate_unique_violation(exc)
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    @override
    async def increment_books_on_hand(self, *, user_id: UUID, max_books_on_hand: int) -> User | None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.books_on_hand < max_books_on_hand)
            .values(books_on_hand=UserModel.books_on_hand + 1)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    @override
    async def decrement_books_on_hand(self, *, user_id: UUID) -> User | None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id, UserModel.books_on_hand > 0)
            .values(books_on_hand=UserModel.books_on_hand - 1)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    @override
    async def delete(self, *, user_id: UUID) -> bool:
        stmt = delete(UserModel).where(UserModel.id == user_id).returning(UserModel.id)
        result = await self._session.execute(stmt)
        deleted_id = result.scalar_one_or_none()
        return deleted_id is not None

    @staticmethod
    def _translate_unique_violation(exc: IntegrityError) -> NoReturn:
        """Convert known Postgres unique-constraint names into domain errors."""
        message = str(exc.orig).lower() if exc.orig is not None else ""
        if "users_username_key" in message:
            raise UsernameAlreadyTakenError() from exc
        if "users_email_key" in message:
            raise EmailAlreadyTakenError() from exc
        raise exc
