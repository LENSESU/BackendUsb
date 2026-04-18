"""Implementación de UserRepositoryPort usando PostgreSQL con SQLAlchemy async."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.infrastructure.db import SyncSessionLocal, get_session

from app.application.ports import UserRepositoryPort
from app.application.ports.user_repository import UserBasicData
from app.domain.entities import User
from app.infrastructure.database.models import UserModel


def _get_session() -> Session:
    return SyncSessionLocal()

class SqlUserRepository(UserRepositoryPort):
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
                first_name=row.first_name,
                last_name=row.last_name,
                role_id=row.role_id,
                is_active=row.is_active,
                created_at=row.created_at,
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
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role_id=user.role_id,
                )
                session.add(instance)
                await session.flush()
                user.id = instance.id
            else:
                instance.email = user.email
                instance.password_hash = user.password_hash
                instance.first_name = user.first_name
                instance.last_name = user.last_name
                instance.role_id = user.role_id
            await session.commit()
            return user

    def get_by_id(self, user_id: UUID) -> UserBasicData | None:
        """Obtiene datos básicos de un usuario por su ID (síncrono)."""
        db = _get_session()
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
