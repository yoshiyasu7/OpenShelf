from inspect import isabstract

from src.domain.repositories.author.main import AuthorRepository
from src.domain.repositories.book.main import BookRepository
from src.domain.repositories.user.main import UserRepository
from src.infrastructure.interfaces.database import DatabaseInterface


def test_author_repository_declares_required_contract() -> None:
    assert isabstract(AuthorRepository)
    assert AuthorRepository.__abstractmethods__ == {
        "create",
        "delete",
        "exists_by_name",
        "get_by_id",
        "get_by_ids",
        "list_paginated",
        "update",
    }


def test_book_repository_declares_required_contract() -> None:
    assert isabstract(BookRepository)
    assert BookRepository.__abstractmethods__ == {
        "create",
        "create_loan",
        "delete",
        "exists_by_title",
        "get_by_id",
        "get_loan_by_id",
        "has_open_loan_for_book",
        "has_overdue_loans",
        "list_open_loans_with_book_titles",
        "list_paginated",
        "mark_loan_returned",
        "return_instance",
        "take_available_instance",
        "update",
    }


def test_user_repository_declares_required_contract() -> None:
    assert isabstract(UserRepository)
    assert UserRepository.__abstractmethods__ == {
        "create",
        "delete",
        "decrement_books_on_hand",
        "exists_by_username_or_email",
        "get_by_id",
        "get_by_identifier",
        "increment_books_on_hand",
        "update",
    }


def test_database_interface_declares_required_contract() -> None:
    assert isabstract(DatabaseInterface)
    assert DatabaseInterface.__abstractmethods__ == {
        "get_session",
        "health_check",
        "initialize",
        "shutdown",
    }
