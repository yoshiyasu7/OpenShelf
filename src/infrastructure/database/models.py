"""SQLAlchemy models."""

import typing as t
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean, DateTime, String, Integer, Text, Column, ForeignKey, JSON
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    """SQLAlchemy model for User entity."""

    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
