"""make before_photo_id nullable on incidents

Revision ID: 003
Revises: 002
Create Date: 2025-03-08

"""
from collections.abc import Sequence

from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "incidents",
        "before_photo_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "incidents",
        "before_photo_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
