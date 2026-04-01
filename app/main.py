"""Punto de entrada de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api import error_handlers
from app.api.routes import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.infrastructure.database.migrations import run_migrations
from app.scripts.seed_users import seed_users

logger = logging.getLogger("uvicorn.error")


def emit_startup_log(message: str) -> None:
    logger.info(message)
    print(f"[startup] {message}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    emit_startup_log(
        "Iniciando startup de la aplicacion "
        f"(migraciones={settings.run_migrations_on_startup}, "
        f"seed_usuarios={settings.seed_users_on_startup})"
    )
    if settings.run_migrations_on_startup:
        emit_startup_log("Ejecutando migraciones de base de datos...")
        run_migrations()
        emit_startup_log("Migraciones completadas correctamente")

    if settings.seed_users_on_startup:
        emit_startup_log("Ejecutando seed de usuarios...")
        seed_users()
        emit_startup_log("Seed de usuarios completado correctamente")

    emit_startup_log("Startup de la aplicacion completado")
    yield


app = FastAPI(
    title="Backend API",
    description="API con arquitectura hexagonal",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, error_handlers.app_error_handler)
app.add_exception_handler(
    RequestValidationError, error_handlers.validation_error_handler
)
app.add_exception_handler(Exception, error_handlers.generic_exception_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
