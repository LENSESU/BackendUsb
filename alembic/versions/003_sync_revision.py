"""sync revision 003 (no-op para BD que ya tenían 003 en alembic_version)

Si la base de datos tenía la revisión '003' registrada pero no existía el archivo,
esta migración vacía permite que 'upgrade head' resuelva correctamente.

Revision ID: 003
Revises: 002
Create Date: 2025-03-12

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # No-op: solo existe para que Alembic resuelva la revisión 003.
    pass


def downgrade() -> None:
    # No-op.
    pass
