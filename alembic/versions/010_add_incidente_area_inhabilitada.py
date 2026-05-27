"""add incidente_area_inhabilitada junction table

Revision ID: 010
Revises: 009
Create Date: 2026-05-26

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "incidente_area_inhabilitada",
        sa.Column("incidente_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("area_inhabilitada_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["incidente_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["area_inhabilitada_id"], ["areas_inhabilitadas.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("incidente_id", "area_inhabilitada_id"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_table("incidente_area_inhabilitada")
