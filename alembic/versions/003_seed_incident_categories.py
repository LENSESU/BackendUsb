"""seed incident categories

Revision ID: 003
Revises: 002
Create Date: 2026-03-09

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


incident_categories = table(
    "incident_categories",
    column("name", sa.String),
    column("description", sa.String),
)


def upgrade() -> None:
    op.bulk_insert(
        incident_categories,
        [
            {
                "name": "Infraestructura",
                "description": "Daños en infraestructura del campus",
            },
            {
                "name": "Eléctrico",
                "description": "Problemas eléctricos como luminarias o cableado",
            },
            {
                "name": "Aseo",
                "description": "Situaciones relacionadas con limpieza o residuos",
            },
            {
                "name": "Seguridad",
                "description": "Incidentes que afectan la seguridad en el campus",
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            DELETE FROM incident_categories
            WHERE name IN (
                'Infraestructura',
                'Eléctrico',
                'Aseo',
                'Seguridad'
            )
            """
        )
    )