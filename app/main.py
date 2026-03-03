"""Punto de entrada de la aplicación FastAPI."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import api_router
from app.core.config import settings
from app.infrastructure.database.migrations import run_migrations

# --- Migraciones al arranque ---
# Al levantar la app se aplican las migraciones a Postgres (tablas al día).
# Solo necesitas: Postgres corriendo + .env con POSTGRES_* (o DATABASE_URL).
# En tests se desactiva con RUN_MIGRATIONS_ON_STARTUP=false (conftest).


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Arranque: aplica migraciones a la BD. Parada: nada."""
    if settings.run_migrations_on_startup:
        run_migrations()
    yield


app = FastAPI(
    title="Backend API",
    description="API con arquitectura hexagonal",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root() -> dict[str, str]:
    """Raíz: enlaces útiles."""
    return {
        "message": "Backend API",
        "docs": "/docs",
        "health": "/health",
        "login": "/api/v1/auth/login",
    }


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de que el servicio está vivo."""
    return {"status": "ok"}
