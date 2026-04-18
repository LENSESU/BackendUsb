"""Configuración de SQLAlchemy async para PostgreSQL."""

import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase,  Session, sessionmaker
from sqlalchemy import create_engine

from app.infrastructure.database.base import Base

# Construimos la URL de la base de datos a partir de variables de entorno,
# con valores por defecto compatibles con el docker-compose.yml.
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "app_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)


# ---------------------------------------------------------------------------
# Engine ASYNC — servicios/rutas async
# ---------------------------------------------------------------------------

async_engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Context manager async — para uso directo con `async with`."""
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Engine SYNC — para auth (JWT es síncrono) y Alembic
# Singleton: creado una sola vez, reutiliza el connection pool.
# ---------------------------------------------------------------------------
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    pool_pre_ping=True,   # descarta conexiones muertas automáticamente
    pool_size=10,
    max_overflow=20,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency síncrono.

    Uso en rutas:
        @router.post("/login")
        def login(db: Session = Depends(get_db)): ...

    El `yield` garantiza que la sesión se cierra al terminar el request,
    incluso si hay una excepción — sin importar si se hace commit o no.
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()