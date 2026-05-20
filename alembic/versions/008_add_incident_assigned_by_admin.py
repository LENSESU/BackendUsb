"""add assigned_by_admin_id to incidents

Revision ID: 008
Revises: 007
Create Date: 2026-04-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("assigned_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_incidents_assigned_by_admin_id_users",
        "incidents",
        "users",
        ["assigned_by_admin_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_incidents_assigned_by_admin_id_users",
        "incidents",
        type_="foreignkey",
    )
    op.drop_column("incidents", "assigned_by_admin_id")
