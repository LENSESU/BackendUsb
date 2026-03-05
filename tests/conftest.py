"""
Configuración global de pytest.
Desactiva migraciones al arranque para que los tests no requieran BD.
"""
import os

# Debe fijarse antes de importar la app para que settings lo tome
os.environ.setdefault("RUN_MIGRATIONS_ON_STARTUP", "false")
