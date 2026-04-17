from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateBookRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=10_000)
    publication_date: date
    genres: list[str] = Field(default_factory=list)
    author_ids: list[UUID] = Field(min_length=1)
    available_instances: int = Field(default=0, ge=0, le=10_000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.split()).strip()


class UpdateBookRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    publication_date: date | None = None
    genres: list[str] | None = None
    available_instances: int | None = Field(default=None, ge=0, le=10_000)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.split()).strip()


class BookAuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    publication_date: date
    genres: list[str]
    authors: list[BookAuthorResponse]
    available_instances: int
    created_at: datetime
    updated_at: datetime


class BooksListResponse(BaseModel):
    items: list[BookResponse]
    total: int
    limit: int
    offset: int


class BookLoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    book_id: UUID
    issued_at: datetime
    due_date: date
    returned_at: datetime | None


class IssueBookResponse(BaseModel):
    loan: BookLoanResponse
    available_instances: int


class ReturnBookResponse(BaseModel):
    loan: BookLoanResponse
    available_instances: int
