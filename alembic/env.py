"""
Entorno de ejecución de Alembic.
Carga la URL desde la configuración de la app y usa los modelos ORM para autogenerate.
"""

import sys
from pathlib import Path

# Añadir raíz del proyecto al path para importar app
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from logging.config import fileConfig  # noqa: E402

from sqlalchemy import engine_from_config, pool  # noqa: E402

from alembic import context  # noqa: E402
from app.infrastructure.database import models  # noqa: E402,F401

# Importar Base y todos los modelos para que target_metadata esté completo
from app.infrastructure.database.base import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Obtiene la URL de la base de datos desde la configuración de la app."""
    from app.core.config import settings

    return settings.database_url_sync


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline (genera SQL sin conectar)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online (conexión real a la BD)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
