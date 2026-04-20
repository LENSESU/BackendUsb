"""Implementación de UserRepositoryPort usando PostgreSQL con SQLAlchemy."""

from uuid import UUID

from sqlalchemy import select

from app.application.ports.user_repository import UserBasicData, UserRepositoryPort
from app.domain.entities import User
from app.domain.entities.role import Role
from app.infrastructure.database.models import RoleModel, UserModel
from app.infrastructure.db import SyncSessionLocal, get_session


def _model_to_entity(row: UserModel) -> User:
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


class SqlUserRepository(UserRepositoryPort):
    """Repositorio de usuarios en PostgreSQL."""

    # ------------------------------------------------------------------
    # Async
    # ------------------------------------------------------------------

    async def get_by_email(self, email: str) -> User | None:
        async with get_session() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _model_to_entity(row) if row else None

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

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def get_by_email_sync(self, email: str) -> User | None:
        db = SyncSessionLocal()
        try:
            row = db.scalar(select(UserModel).where(UserModel.email == email))
            return _model_to_entity(row) if row else None
        finally:
            db.close()

    def get_by_id(self, user_id: UUID) -> UserBasicData | None:
        db = SyncSessionLocal()
        try:
            model = db.scalar(select(UserModel).where(UserModel.id == user_id))
            if model is None:
                return None
            return UserBasicData(
                id=model.id,
                first_name=model.first_name,
                last_name=model.last_name,
                email=model.email,
            )
        finally:
            db.close()

    def get_role_name_by_id(self, role_id: UUID) -> str | None:
        db = SyncSessionLocal()
        try:
            role = db.scalar(select(RoleModel).where(RoleModel.id == role_id))
            return role.name if role else None
        finally:
            db.close()

    def save_sync(self, user: User) -> User:
        db = SyncSessionLocal()
        try:
            instance: UserModel | None = None
            if user.id is not None:
                instance = db.scalar(select(UserModel).where(UserModel.id == user.id))
            if instance is None:
                instance = UserModel(
                    email=user.email,
                    password_hash=user.password_hash,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role_id=user.role_id,
                    is_active=user.is_active,
                )
                db.add(instance)
                db.flush()
                user.id = instance.id
            else:
                instance.email = user.email
                instance.password_hash = user.password_hash
                instance.first_name = user.first_name
                instance.last_name = user.last_name
                instance.role_id = user.role_id
                instance.is_active = user.is_active
            db.commit()
            db.refresh(instance)
            return user
        finally:
            db.close()

    def get_role_by_name(self, name: str) -> Role | None:
        db = SyncSessionLocal()
        try:
            model = db.scalar(select(RoleModel).where(RoleModel.name == name))
            if model is None:
                return None
            return Role(id=model.id, name=model.name, description=model.description)
        finally:
            db.close()

    def get_role_by_id(self, role_id: UUID) -> Role | None:
        db = SyncSessionLocal()
        try:
            model = db.scalar(select(RoleModel).where(RoleModel.id == role_id))
            if model is None:
                return None
            return Role(id=model.id, name=model.name, description=model.description)
        finally:
            db.close()

    def delete_sync(self, user: User) -> None:
        db = SyncSessionLocal()
        try:
            if user.id is None:
                return
            instance = db.scalar(select(UserModel).where(UserModel.id == user.id))
            if instance is not None:
                db.delete(instance)
                db.commit()
        finally:
            db.close()
