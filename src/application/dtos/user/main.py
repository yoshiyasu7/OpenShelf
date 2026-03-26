from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None
    is_admin: bool


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class RegisterResponse(BaseModel):
    user: UserPublic


class TokenResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    refresh_token: str
    user: UserPublic
