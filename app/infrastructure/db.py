"""Configuración de SQLAlchemy async para PostgreSQL."""
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine ASYNC — servicios/rutas async
# ---------------------------------------------------------------------------
async_engine = create_async_engine(settings.database_url_async, echo=False)
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
# ---------------------------------------------------------------------------
sync_engine = create_engine(
    settings.database_url_sync,  # 👈 siempre postgresql:// limpio
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency síncrono."""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()