from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.dtos.user.main import UserPublic
from src.dependencies import ValidateTokenService  # noqa: TC001
from src.domain.exceptions.user import InvalidCredentialsError, UserNotFoundError

if TYPE_CHECKING:
    from uuid import UUID

    from src.domain.repositories.user.main import UserRepository
    from src.infrastructure.database.models import UserModel

TokenAuth = Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))]


# Dependencies for protected endpoints
async def get_current_user(
    credentials: TokenAuth,
    uc: ValidateTokenService,
) -> UserPublic:
    """Resolve authenticated user from bearer access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        return UserPublic.model_validate(await uc.execute(access_token=credentials.credentials))
    except (InvalidCredentialsError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def get_current_admin(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    """Resolve authenticated admin user."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return current_user


CurrentUserDep = Annotated[UserPublic, Depends(get_current_user)]
AdminUserDep = Annotated[UserPublic, Depends(get_current_admin)]


class UserUseCases:
    """
    """

    def __init__(self, *, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def get_user(self, *, user_id: UUID) -> UserModel:
        found_user = await self._user_repository.get_by_id(user_id=user_id)
        if not found_user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        return found_user

    async def update_user(self, *, user: UserPublic) -> UserModel:
        ...
