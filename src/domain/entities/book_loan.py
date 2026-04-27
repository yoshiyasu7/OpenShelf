"""BookLoan domain entity."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date, datetime
    from uuid import UUID


@dataclass
class BookLoan:
    """Domain model describing an active or closed book loan."""

    id: UUID
    user_id: UUID
    book_id: UUID
    issued_at: datetime
    due_date: date
    returned_at: datetime | None
    created_at: datetime
    updated_at: datetime
