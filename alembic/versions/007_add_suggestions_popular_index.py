"""add index for popular suggestions query

Revision ID: 007
Revises: 006
Create Date: 2026-03-20
"""

from collections.abc import Sequence

from alembic import op

revision: str = "007"
down_revision: str | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_suggestions_total_votes_created_at",
        "suggestions",
        ["total_votes", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_suggestions_total_votes_created_at", table_name="suggestions")
