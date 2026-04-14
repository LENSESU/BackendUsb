"""Implementación de UserRepositoryPort usando PostgreSQL con SQLAlchemy async."""

from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.application.ports import UserRepositoryPort
from app.application.ports.user_repository import UserBasicData
from app.core.config import settings
from app.domain.entities import User, UserRole
from app.infrastructure.db import get_session
from app.infrastructure.models.user_model import UserModel


def _get_session_sync():
    """Crea una sesión síncrona."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class PostgresUserRepository(UserRepositoryPort):
    """Repositorio de usuarios en PostgreSQL."""

    async def get_by_email(self, email: str) -> User | None:
        async with get_session() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return User(
                id=row.id,
                email=row.email,
                password_hash=row.password_hash,
                name=row.name,
                role=UserRole(row.role),
            )

    async def save(self, user: User) -> User:
        async with get_session() as session:
            instance: UserModel | None = None
            if user.id is not None:
                instance = await session.get(UserModel, user.id)

            if instance is None:
                instance = UserModel(
                    email=user.email,
                    password_hash=user.password_hash,
                    name=user.name,
                    role=user.role.value,
                )
                session.add(instance)
                await session.flush()  # para obtener el id autogenerado
                user.id = instance.id
            else:
                instance.email = user.email
                instance.password_hash = user.password_hash
                instance.name = user.name
                instance.role = user.role.value

            await session.commit()
            return user

    def get_by_id(self, user_id: UUID) -> UserBasicData | None:
        """Obtiene datos básicos de un usuario por su ID (síncrono)."""
        db = _get_session_sync()
        try:
            stmt = select(UserModel).where(UserModel.id == user_id)
            model = db.scalar(stmt)
            if model:
                return UserBasicData(
                    id=model.id,
                    first_name=model.first_name,
                    last_name=model.last_name,
                    email=model.email,
                )
            return None
        finally:
            db.close()
