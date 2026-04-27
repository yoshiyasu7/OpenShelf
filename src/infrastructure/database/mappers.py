"""ORM <-> domain entity mappers.

These functions isolate the SQLAlchemy layer from the rest of the application:
repositories return pure domain entities, so use cases never see ORM models.
"""

from typing import TYPE_CHECKING

from src.domain.entities import Author, Book, BookLoan, RefreshSession, User

if TYPE_CHECKING:
    from src.infrastructure.database.models import (
        AuthorModel,
        BookLoanModel,
        BookModel,
        RefreshSessionModel,
        UserModel,
    )


def user_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        username=model.username,
        email=model.email,
        password_hash=model.password_hash,
        is_admin=model.is_admin,
        books_on_hand=model.books_on_hand,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def author_to_entity(model: AuthorModel, *, include_books: bool = True) -> Author:
    return Author(
        id=model.id,
        name=model.name,
        biography=model.biography,
        birthday=model.birthday,
        created_at=model.created_at,
        updated_at=model.updated_at,
        books=([book_to_entity(book, include_authors=False) for book in (model.books or [])] if include_books else []),
    )


def book_to_entity(model: BookModel, *, include_authors: bool = True) -> Book:
    return Book(
        id=model.id,
        title=model.title,
        description=model.description,
        publication_date=model.publication_date,
        genres=list(model.genres or []),
        available_instances=model.available_instances,
        created_at=model.created_at,
        updated_at=model.updated_at,
        authors=(
            [author_to_entity(author, include_books=False) for author in (model.authors or [])]
            if include_authors
            else []
        ),
    )


def book_loan_to_entity(model: BookLoanModel) -> BookLoan:
    return BookLoan(
        id=model.id,
        user_id=model.user_id,
        book_id=model.book_id,
        issued_at=model.issued_at,
        due_date=model.due_date,
        returned_at=model.returned_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def refresh_session_to_entity(model: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        id=model.id,
        user_id=model.user_id,
        token_hash=model.token_hash,
        created_at=model.created_at,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
    )
