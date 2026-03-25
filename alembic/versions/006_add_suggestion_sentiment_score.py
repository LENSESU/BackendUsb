"""add sentiment_score to suggestions

Revision ID: 006
Revises: 005
Create Date: 2026-03-20

Columna opcional para análisis de sentimiento futuro (-1..1 típico).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "suggestions",
        sa.Column("sentiment_score", sa.Numeric(precision=5, scale=4), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("suggestions", "sentiment_score")
