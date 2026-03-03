"""Configuración de SQLAlchemy async para PostgreSQL."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/mydatabase",
)

engine = create_async_engine(DATABASE_URL, echo=False)


class Base(DeclarativeBase):
    """Base para modelos de SQLAlchemy."""

    pass


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """Provee una sesión async de SQLAlchemy."""
    async with AsyncSessionLocal() as session:
        yield session

