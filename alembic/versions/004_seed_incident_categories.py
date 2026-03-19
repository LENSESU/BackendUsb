"""seed incident categories

Revision ID: 004
Revises: 003
Create Date: 2026-03-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.sql import column, table

from alembic import op

# revision identifiers
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


incident_categories = table(
    "incident_categories",
    column("name", sa.String),
    column("description", sa.String),
)


def upgrade() -> None:
    # Idempotencia: si la categoría ya existe (UNIQUE por name), no debe fallar la migración.
    # Elegimos DO UPDATE para mantener la descripción sincronizada con la "fuente de verdad" del seed.
    op.execute(
        sa.text(
            """
            INSERT INTO incident_categories (name, description)
            VALUES
                ('Infraestructura', 'Daños en infraestructura del campus'),
                ('Eléctrico', 'Problemas eléctricos como luminarias o cableado'),
                ('Aseo', 'Situaciones relacionadas con limpieza o residuos'),
                ('Seguridad', 'Incidentes que afectan la seguridad en el campus')
            ON CONFLICT (name) DO UPDATE
            SET description = EXCLUDED.description
            """
        )
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
