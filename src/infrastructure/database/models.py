"""SQLAlchemy models."""

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Boolean, Index,
    String, Integer, Table, Text, Column, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY


class Base(DeclarativeBase):
    pass


authors_books = Table(
    "authors_books",
    Base.metadata,
    Column("book_id", UUID, ForeignKey("books.id", ondelete='CASCADE'), primary_key=True, index=True),
    Column("author_id", UUID, ForeignKey("authors.id"), primary_key=True, index=True),
)


class UserModel(Base):
    """SQLAlchemy model for User entity."""

    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    books_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )


class AuthorModel(Base):
    """SQLAlchemy model for Author entity."""

    __tablename__ = 'authors'

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String)
    biography: Mapped[str] = mapped_column(Text)
    birthday: Mapped[date] = mapped_column(Date, index=True)
    books: Mapped[list["BookModel"]] = relationship(
        secondary="authors_books",
        back_populates="authors",
        lazy="selectin",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )
    
    __table_args__ = (
        CheckConstraint("birthday <= CURRENT_DATE", name="check_birthday_not_future"),
    )


class BookModel(Base):
    """SQLAlchemy model for Book entity."""

    __tablename__ = 'books'

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    publication_date: Mapped[date] = mapped_column(Date, index=True)
    authors: Mapped[list["AuthorModel"]] = relationship(
        secondary="authors_books",
        back_populates="books",
        lazy="selectin",
    )
    genres: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    available_instances: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )
    
    __table_args__ = (
        CheckConstraint("publication_date <= CURRENT_DATE", name="check_publication_date_not_future"),
        CheckConstraint("available_instances >= 0", name="check_available_instances_not_negative"),
    )


class BookLoanModel(Base):
    """SQLAlchemy model for loan/borrowing Book entity."""

    __tablename__ = "book_loans"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_id: Mapped[UUID] = mapped_column(
        UUID,
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False,
        index=True,
    )
    due_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone.utc),
        onupdate=lambda: datetime.now(tz=timezone.utc),
        nullable=False
    )

    user: Mapped["UserModel"] = relationship(lazy="selectin")
    book: Mapped["BookModel"] = relationship(lazy="selectin")

    __table_args__ = (
        # return_at only after issued_at
        CheckConstraint("returned_at IS NULL OR returned_at >= issued_at", name="check_returned_after_issued"),
        # due_date only after issued_at
        CheckConstraint("due_date >= issued_at::date", name="check_due_after_issue"),
        # Opened loans for a user or book.
        Index("idx_book_loans_user_open", "user_id", postgresql_where=(Column("returned_at") == None)),
        Index("idx_book_loans_book_open", "book_id", postgresql_where=(Column("returned_at") == None)),
    )