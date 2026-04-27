from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from src.application.dtos.user.main import UserPublic
from src.infrastructure.database.models import AuthorModel, BookLoanModel, BookModel


def make_author_model(
    *,
    author_id: UUID | None = None,
    name: str = "Leo Tolstoy",
    biography: str = "Russian writer",
    birthday: date = date(1828, 9, 9),
    books: list[BookModel] | None = None,
) -> AuthorModel:
    now = datetime.now(UTC)
    author = AuthorModel(
        id=author_id or uuid4(),
        name=name,
        biography=biography,
        birthday=birthday,
        created_at=now,
        updated_at=now,
    )
    author.books = books or []
    return author


def make_user_public(*, is_admin: bool) -> UserPublic:
    return UserPublic(
        id=uuid4(),
        username="test-user",
        email="test@example.com",
        is_admin=is_admin,
    )


def make_book_model(
    *,
    book_id: UUID | None = None,
    title: str = "War and Peace",
    description: str = "Classic novel",
    publication_date: date = date(1869, 1, 1),
    genres: list[str] | None = None,
    available_instances: int = 3,
    authors: list[AuthorModel] | None = None,
) -> BookModel:
    now = datetime.now(UTC)
    book = BookModel(
        id=book_id or uuid4(),
        title=title,
        description=description,
        publication_date=publication_date,
        genres=genres or ["classic"],
        available_instances=available_instances,
        created_at=now,
        updated_at=now,
    )
    book.authors = authors or []
    return book


def make_book_loan_model(
    *,
    loan_id: UUID | None = None,
    user_id: UUID | None = None,
    book_id: UUID | None = None,
    due_date: date = date(2026, 5, 1),
    returned_at: datetime | None = None,
) -> BookLoanModel:
    now = datetime.now(UTC)
    return BookLoanModel(
        id=loan_id or uuid4(),
        user_id=user_id or uuid4(),
        book_id=book_id or uuid4(),
        issued_at=now,
        due_date=due_date,
        returned_at=returned_at,
        created_at=now,
        updated_at=now,
    )
