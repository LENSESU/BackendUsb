"""add theme_preference to users

Revision ID: 011
Revises: 010
Create Date: 2026-06-01

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "theme_preference",
            sa.String(length=10),
            nullable=False,
            server_default=sa.text("'light'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "theme_preference")
