"""seed incident categories

Revision ID: 6e9c57dc30d5
Revises: 002
Create Date: 2026-03-09 18:24:38.561691

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e9c57dc30d5'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO incident_categories (name, description) VALUES
        ('Infraestructura', 'Daños en infraestructura del campus'),
        ('Eléctrico', 'Problemas eléctricos como luminarias o cableado'),
        ('Aseo', 'Situaciones relacionadas con limpieza o residuos'),
        ('Seguridad', 'Incidentes que afectan la seguridad en el campus');
    """)

def downgrade() -> None:
    op.execute("""
        DELETE FROM incident_categories
        WHERE name IN (
            'Infraestructura',
            'Eléctrico',
            'Aseo',
            'Seguridad'
        );
    """)