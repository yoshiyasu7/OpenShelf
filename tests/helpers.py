from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.application.dtos.user.main import UserPublic
from src.infrastructure.database.models import AuthorModel


def make_author_model(
    *,
    author_id: UUID | None = None,
    name: str = "Leo Tolstoy",
    biography: str = "Russian writer",
    birthday: date = date(1828, 9, 9),
) -> AuthorModel:
    now = datetime.now(UTC)
    return AuthorModel(
        id=author_id or uuid4(),
        name=name,
        biography=biography,
        birthday=birthday,
        created_at=now,
        updated_at=now,
    )


def make_user_public(*, is_admin: bool) -> UserPublic:
    return UserPublic(
        id=uuid4(),
        username="test-user",
        email="test@example.com",
        is_admin=is_admin,
    )
