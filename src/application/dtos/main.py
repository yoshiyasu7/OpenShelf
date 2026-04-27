from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime
    from uuid import UUID


class QueryFilterParams(BaseModel):
    limit: int = Field(10, ge=1, le=100, description="Max results (1-100, default: 10)")
    offset: int = Field(0, ge=0, description="Results to skip")
    name_query: str | None = Field(None, description="Search by name (partial match)")


@dataclass(slots=True, frozen=True)
class PaginatedResult[T]:
    items: list[T]
    total: int
    limit: int
    offset: int


@dataclass(slots=True, frozen=True)
class OpenLoanItem:
    loan_id: UUID
    book_id: UUID
    title: str | None
    issued_at: datetime
    due_date: date
