from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreateAuthorRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    biography: str = Field(min_length=1, max_length=10_000)
    birthday: date

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.split()).strip()


class UpdateAuthorRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    biography: str | None = Field(default=None, min_length=1, max_length=10_000)
    birthday: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.split()).strip()


class AuthorBookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    publication_date: date
    available_instances: int


class AuthorCreateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    biography: str
    birthday: date
    created_at: datetime
    updated_at: datetime


class AuthorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    biography: str
    birthday: date
    books: list[AuthorBookResponse]
    created_at: datetime
    updated_at: datetime


class AuthorsListResponse(BaseModel):
    items: list[AuthorResponse]
    total: int
    limit: int
    offset: int
