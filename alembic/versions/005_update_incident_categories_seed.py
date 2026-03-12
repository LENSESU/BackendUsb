"""update incident categories seed

Revision ID: 005
Revises: 004
Create Date: 2026-03-12

Esta migración actualiza los datos sembrados por la revisión 004
para la tabla ``incident_categories``.

Reglas:
- No modifica la estructura de la tabla.
- Solo realiza operaciones de INSERT ... ON CONFLICT para mantener
  las categorías sincronizadas con la fuente de verdad de negocio.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Actualiza/ajusta las categorías de incidentes sembradas previamente.

    Propósito:
        - Permitir ajustar textos de descripción sin tocar la migración 004.
        - Mantener idempotencia usando ON CONFLICT (name).
        - Facilitar la incorporación de nuevas categorías si es necesario.

    Nota:
        - Si alguna de estas categorías ya existe, se actualiza únicamente
          su descripción.
        - Si no existe, se inserta.
    """
    op.execute(
        sa.text(
            """
            INSERT INTO incident_categories (name, description)
            VALUES
                ('Infraestructura', 'Daños o fallas en la infraestructura del campus (paredes, techos, mobiliario, etc.)'),
                ('Eléctrico', 'Problemas eléctricos como luminarias dañadas, tomacorrientes defectuosos o cableado expuesto'),
                ('Aseo', 'Situaciones relacionadas con limpieza, acumulación de residuos o malas condiciones higiénicas'),
                ('Seguridad', 'Incidentes que afectan la seguridad personal o patrimonial dentro del campus'),
                ('Otro', 'Incidentes que no encajan claramente en las categorías anteriores')
            ON CONFLICT (name) DO UPDATE
            SET description = EXCLUDED.description
            """
        )
    )


def downgrade() -> None:
    """Revierte únicamente los cambios introducidos en esta revisión.

    - Elimina la categoría adicional introducida en esta migración.
    - Restaura las descripciones anteriores para las categorías
      existentes según la migración 004.
    """
    # Eliminar la categoría agregada en esta revisión.
    op.execute(
        sa.text(
            """
            DELETE FROM incident_categories
            WHERE name = 'Otro'
            """
        )
    )

    # Restaurar descripciones originales definidas en 004.
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

