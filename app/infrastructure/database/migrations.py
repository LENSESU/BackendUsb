"""
Al arrancar la app se llama a run_migrations() → aplica todas las migraciones
pendientes a Postgres (crea/actualiza tablas). Equivale a ejecutar por terminal:
  alembic upgrade head
"""

import logging
import os
from pathlib import Path

from alembic.config import Config

from alembic import command

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Aplica migraciones pendientes (upgrade head) usando la URL de la app."""

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    alembic_ini_path = project_root / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"No se encuentra alembic.ini en {project_root}")

    os.chdir(project_root)

    try:
        alembic_cfg = Config(str(alembic_ini_path))
        command.upgrade(alembic_cfg, "head")

        logger.info("Migraciones aplicadas correctamente")

    except Exception as e:
        logger.error(f"Error ejecutando migraciones: {e}")
