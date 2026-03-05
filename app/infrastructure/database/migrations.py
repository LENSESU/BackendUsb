"""
Al arrancar la app se llama a run_migrations() → aplica todas las migraciones
pendientes a Postgres (crea/actualiza tablas). Equivale a ejecutar por terminal:
  alembic upgrade head
"""

import os
import sys
from pathlib import Path


def run_migrations() -> None:
    """Aplica migraciones pendientes (upgrade head) usando la URL de la app."""
    try:
        from alembic.config import Config
        from alembic import command
    except ImportError:
        print(
            "Aviso: alembic no está instalado en este intérprete; se omiten migraciones. "
            "Ejecuta la app con el Python del venv: .venv\\Scripts\\python.exe -m uvicorn app.main:app --reload",
            file=sys.stderr,
        )
        return

    # Raíz del proyecto (alembic.ini). Subimos 4 niveles desde esta ruta.
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    alembic_ini_path = project_root / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"No se encuentra alembic.ini en {project_root}")

    os.chdir(project_root)
    alembic_cfg = Config(str(alembic_ini_path))
    command.upgrade(alembic_cfg, "head")
