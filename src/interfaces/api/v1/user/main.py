from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, status

from src.application.dtos.user.main import UpdateUserRequest, UserPublic
from src.dependencies import AdminUserDep, CurrentUserDep, UserService  # noqa: TC001

router = APIRouter(
    tags=["Users"],
    prefix="/users",
)


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: CurrentUserDep,
    uc: UserService
) -> UserPublic:
    user = await uc.get_user(user_id=current_user.id)
    return UserPublic.model_validate(user)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    current_user: CurrentUserDep,
    payload: UpdateUserRequest,
    uc: UserService
) -> UserPublic:
    user = await uc.update_user(user_id=current_user.id, payload=payload)
    return UserPublic.model_validate(user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_me(
    current_user: CurrentUserDep,
    uc: UserService
) -> None:
    await uc.delete_user(user_id=current_user.id)


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    _admin: AdminUserDep,
    user_id: UUID,
    uc: UserService
) -> UserPublic:
    user = await uc.get_user(user_id=user_id)
    return UserPublic.model_validate(user)


@router.patch("/{user_id}", response_model=UserPublic)
async def update_user(
    _admin: AdminUserDep,
    user_id: UUID,
    payload: UpdateUserRequest,
    uc: UserService
) -> UserPublic:
    user = await uc.update_user(user_id=user_id, payload=payload)
    return UserPublic.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    _admin: AdminUserDep,
    user_id: UUID,
    uc: UserService
) -> None:
    await uc.delete_user(user_id=user_id)
