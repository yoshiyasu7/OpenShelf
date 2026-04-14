from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from src.domain.exceptions.user import (
    EmailAlreadyTakenError,
    UsernameAlreadyTakenError,
    UserNotFoundError,
)

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.dtos.user.main import UpdateUserRequest
    from src.domain.repositories.user.main import UserRepository
    from src.infrastructure.database.models import UserModel


class UserUseCases:
    """
    Core logic for managing user accounts and profiles.
    This class handles finding, updating, and deleting users.

    Notes:
    - Ensures consistent state through atomic database operations.
    - Translates infrastructure-level integrity violations into domain exceptions.
    """

    def __init__(self, *, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def get_user(self, *, user_id: UUID) -> UserModel:
        found_user = await self._user_repository.get_by_id(user_id=user_id)
        if not found_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        return found_user

    async def update_user(self, *, user_id: UUID, payload: UpdateUserRequest) -> UserModel:
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            user = await self._user_repository.get_by_id(user_id=user_id)
            if not user:
                raise UserNotFoundError(f"User with id {user_id} not found")
            return user
        try:
            user = await self._user_repository.update(user_id=user_id, data=update_data)
            if not user:
                raise UserNotFoundError(f"User with id {user_id} not found")
            return user
        except IntegrityError as e:
            error_msg = str(e.orig).lower()
            if "users_username_key" in error_msg:
                raise UsernameAlreadyTakenError() from e
            if "users_email_key" in error_msg:
                raise EmailAlreadyTakenError() from e
            raise e

    async def delete_user(self, *, user_id: UUID) -> None:
        deleted = await self._user_repository.delete(user_id=user_id)
        if not deleted:
            raise UserNotFoundError(f"User with id {user_id} not found")
