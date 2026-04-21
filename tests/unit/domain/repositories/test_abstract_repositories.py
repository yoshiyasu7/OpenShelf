from uuid import uuid4

import pytest

from src.domain.repositories.author.main import AuthorRepository
from src.domain.repositories.book.main import BookRepository
from src.domain.repositories.user.main import UserRepository
from src.infrastructure.interfaces.database import DatabaseInterface


@pytest.mark.asyncio
async def test_author_repository_abstract_methods_are_callable() -> None:
    assert await AuthorRepository.get_by_id(object(), author_id=uuid4()) is None
    assert await AuthorRepository.get_by_ids(object(), author_ids=[]) is None
    assert await AuthorRepository.exists_by_name(object(), name="name") is None
    assert await AuthorRepository.create(object(), data={}) is None
    assert await AuthorRepository.list_paginated(object(), limit=1, offset=0, name_query=None) is None
    assert await AuthorRepository.update(object(), author_id=uuid4(), data={}) is None
    assert await AuthorRepository.delete(object(), author_id=uuid4()) is None


@pytest.mark.asyncio
async def test_book_repository_abstract_methods_are_callable() -> None:
    assert await BookRepository.get_by_id(object(), book_id=uuid4()) is None
    assert await BookRepository.exists_by_title(object(), title="title") is None
    assert await BookRepository.create(object(), data={}) is None
    assert await BookRepository.list_paginated(object(), limit=1, offset=0, name_query=None) is None
    assert await BookRepository.update(object(), book_id=uuid4(), data={}) is None
    assert await BookRepository.delete(object(), book_id=uuid4()) is None
    assert await BookRepository.has_overdue_loans(object(), user_id=uuid4(), as_of=None) is None
    assert await BookRepository.take_available_instance(object(), book_id=uuid4()) is None
    assert await BookRepository.return_instance(object(), book_id=uuid4()) is None
    assert await BookRepository.create_loan(object(), user_id=uuid4(), book_id=uuid4(), due_date=None) is None
    assert await BookRepository.get_loan_by_id(object(), loan_id=uuid4()) is None
    assert await BookRepository.get_open_loan_by_id(object(), loan_id=uuid4()) is None
    assert await BookRepository.mark_loan_returned(object(), loan_id=uuid4()) is None


@pytest.mark.asyncio
async def test_user_repository_abstract_methods_are_callable() -> None:
    assert await UserRepository.get_by_id(object(), user_id=uuid4()) is None
    assert await UserRepository.get_by_identifier(object(), identifier="id") is None
    assert await UserRepository.exists_by_username_or_email(object(), username="u", email=None) is None
    assert await UserRepository.create(object(), username="u", email=None, password_hash="h") is None
    assert await UserRepository.update(object(), user_id=uuid4(), data={}) is None
    assert await UserRepository.delete(object(), user_id=uuid4()) is None


@pytest.mark.asyncio
async def test_database_interface_abstract_methods_are_callable() -> None:
    assert await DatabaseInterface.initialize(object()) is None
    assert await DatabaseInterface.shutdown(object()) is None
    assert DatabaseInterface.get_session(object()) is None
    assert await DatabaseInterface.health_check(object()) is None
