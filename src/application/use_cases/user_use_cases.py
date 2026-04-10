from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.dtos.user.main import UserPublic  # noqa: TC001
from src.application.mappers.user import user_to_public_dto
from src.dependencies import ValidateTokenService  # noqa: TC001
from src.domain.exceptions.user import InvalidCredentialsError, UserNotFoundError

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
        return user_to_public_dto(await uc.execute(access_token=credentials.credentials))
    except (InvalidCredentialsError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


async def get_current_admin(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    """Resolve authenticated admin user."""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return current_user
