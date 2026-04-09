from typing import TYPE_CHECKING

from src.application.dtos.user.main import UserPublic

if TYPE_CHECKING:
    from src.infrastructure.database.models import UserModel


def user_to_public_dto(u: UserModel) -> UserPublic:
    return UserPublic(
        id=u.id,
        username=u.username,
        email=u.email,
        is_admin=u.is_admin,
    )
