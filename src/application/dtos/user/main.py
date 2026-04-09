from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None
    is_admin: bool
