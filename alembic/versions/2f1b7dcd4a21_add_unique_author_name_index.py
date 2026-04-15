"""Harden authors constraints and unique name index.

Revision ID: 2f1b7dcd4a21
Revises: 095a14abdacd
Create Date: 2026-04-15 19:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f1b7dcd4a21"
down_revision: Union[str, Sequence[str], None] = "095a14abdacd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "authors",
        "name",
        existing_type=sa.String(),
        type_=sa.String(length=200),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "check_authors_name_not_blank",
        "authors",
        "char_length(btrim(name)) > 0",
    )
    op.create_check_constraint(
        "check_authors_biography_max_length",
        "authors",
        "char_length(biography) <= 10000",
    )
    op.create_index(
        "ux_authors_name_lower",
        "authors",
        [sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ux_authors_name_lower", table_name="authors")
    op.drop_constraint("check_authors_biography_max_length", "authors", type_="check")
    op.drop_constraint("check_authors_name_not_blank", "authors", type_="check")
    op.alter_column(
        "authors",
        "name",
        existing_type=sa.String(length=200),
        type_=sa.String(),
        existing_nullable=False,
    )
