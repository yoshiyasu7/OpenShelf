"""User domain entity."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


@dataclass
class User:
    """Domain model describing a library user."""

    id: UUID
    username: str
    email: str | None
    password_hash: str
    is_admin: bool
    books_on_hand: int
    created_at: datetime
    updated_at: datetime
