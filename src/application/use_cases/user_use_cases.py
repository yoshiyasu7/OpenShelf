from typing import TYPE_CHECKING

from src.domain.exceptions.user import UserNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from src.application.dtos.user.main import UpdateUserRequest
    from src.domain.entities import User
    from src.domain.repositories.user.main import UserRepository


class UserUseCases:
    """
    Core logic for managing user accounts and profiles.

    Notes:
    - Conflict translation (IntegrityError -> domain error) lives in the repository,
      so this class stays free of ORM/SQL driver details.
    """

    def __init__(self, *, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def get_user(self, *, user_id: UUID) -> User:
        found_user = await self._user_repository.get_by_id(user_id=user_id)
        if not found_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        return found_user

    async def update_user(self, *, user_id: UUID, payload: UpdateUserRequest) -> User:
        update_data = payload.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_user(user_id=user_id)

        user = await self._user_repository.update(user_id=user_id, data=update_data)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        return user

    async def delete_user(self, *, user_id: UUID) -> None:
        deleted = await self._user_repository.delete(user_id=user_id)
        if not deleted:
            raise UserNotFoundError(f"User with id {user_id} not found")
