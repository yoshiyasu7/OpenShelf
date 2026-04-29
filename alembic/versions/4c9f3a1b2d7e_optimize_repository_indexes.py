"""Optimize repository lookup indexes.

Revision ID: 4c9f3a1b2d7e
Revises: 2f1b7dcd4a21
Create Date: 2026-04-29 17:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4c9f3a1b2d7e"
down_revision: Union[str, Sequence[str], None] = "2f1b7dcd4a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    with op.get_context().autocommit_block():
        op.create_index(
            "ux_books_title_lower",
            "books",
            [sa.text("lower(title)")],
            unique=True,
            postgresql_concurrently=True,
        )
        op.create_index(
            "idx_authors_name_trgm",
            "authors",
            ["name"],
            unique=False,
            postgresql_concurrently=True,
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        )
        op.create_index(
            "idx_books_title_trgm",
            "books",
            ["title"],
            unique=False,
            postgresql_concurrently=True,
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        )
        op.create_index(
            "idx_book_loans_user_open_due_date",
            "book_loans",
            ["user_id", "due_date"],
            unique=False,
            postgresql_concurrently=True,
            postgresql_where=sa.text("returned_at IS NULL"),
        )
        op.create_index(
            "ux_book_loans_user_book_open",
            "book_loans",
            ["user_id", "book_id"],
            unique=True,
            postgresql_concurrently=True,
            postgresql_where=sa.text("returned_at IS NULL"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.get_context().autocommit_block():
        op.drop_index(
            "ux_book_loans_user_book_open",
            table_name="book_loans",
            postgresql_concurrently=True,
        )
        op.drop_index(
            "idx_book_loans_user_open_due_date",
            table_name="book_loans",
            postgresql_concurrently=True,
        )
        op.drop_index("idx_books_title_trgm", table_name="books", postgresql_concurrently=True)
        op.drop_index("idx_authors_name_trgm", table_name="authors", postgresql_concurrently=True)
        op.drop_index("ux_books_title_lower", table_name="books", postgresql_concurrently=True)
