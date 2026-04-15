"""Implementación de UserRepositoryPort usando PostgreSQL con SQLAlchemy async."""

from sqlalchemy import select

from app.application.ports import UserRepositoryPort
from app.domain.entities import User
from app.domain.entities.role import Role
from app.infrastructure.db import get_session
from app.infrastructure.models.user_model import UserModel


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
                role=Role(row.role),
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
                    name=user.first_name + " " + user.last_name,
                    role=user.role_id,
                )
                session.add(instance)
                await session.flush()  # para obtener el id autogenerado
                user.id = instance.id
            else:
                instance.email = user.email
                instance.password_hash = user.password_hash
                instance.name = (user.first_name + " " + user.last_name,)
                instance.role = user.role_id

            await session.commit()
            return user
