from uuid import UUID

from pydantic import BaseModel


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: str | None = None
    is_admin: bool
