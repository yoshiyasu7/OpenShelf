"""Catalog domain entities."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date, datetime
    from uuid import UUID


@dataclass
class Author:
    """Domain model describing a book author."""

    id: UUID
    name: str
    biography: str
    birthday: date
    created_at: datetime
    updated_at: datetime
    books: list[Book] = field(default_factory=list)


@dataclass
class Book:
    """Domain model describing a book in the catalog."""

    id: UUID
    title: str
    description: str
    publication_date: date
    genres: list[str]
    available_instances: int
    created_at: datetime
    updated_at: datetime
    authors: list[Author] = field(default_factory=list)
