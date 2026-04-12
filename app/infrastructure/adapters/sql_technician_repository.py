"""Adaptador SQLAlchemy para el puerto de técnicos (usuarios con rol Technician)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import create_engine, exists, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.technician_repository import TechnicianRepositoryPort
from app.core.config import settings
from app.domain.entities.incident import IncidentStatus
from app.domain.entities.user import User
from app.infrastructure.database.models import IncidentModel, RoleModel, UserModel

TECHNICIAN_ROLE_NAME = "Technician"


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _user_model_to_entity(row: UserModel) -> User:
    """Mapeo de fila ORM de usuario a entidad de dominio."""
    return User(
        id=row.id,
        first_name=row.first_name,
        last_name=row.last_name,
        email=row.email,
        password_hash=row.password_hash,
        role_id=row.role_id,
        is_active=row.is_active,
        created_at=row.created_at,
    )


def _technician_user_stmt():
    """Subconsulta base: usuarios cuyo rol es técnico."""
    return (
        select(UserModel)
        .join(RoleModel, UserModel.role_id == RoleModel.id)
        .where(RoleModel.name == TECHNICIAN_ROLE_NAME)
    )


class SqlTechnicianRepository(TechnicianRepositoryPort):
    """Persistencia de técnicos y asignación a incidentes vía SQLAlchemy síncrono."""

    def find_all(self) -> list[User]:
        db = _get_session()
        try:
            stmt = _technician_user_stmt().order_by(
                UserModel.last_name, UserModel.first_name
            )
            rows = db.scalars(stmt).all()
            return [_user_model_to_entity(r) for r in rows]
        finally:
            db.close()

    def find_by_id(self, user_id: str) -> User | None:
        db = _get_session()
        try:
            uid = UUID(user_id)
            stmt = _technician_user_stmt().where(UserModel.id == uid)
            row = db.scalar(stmt)
            return _user_model_to_entity(row) if row else None
        finally:
            db.close()

    def assign_technician_to_incident(
        self, technician_id: str, incident_id: str
    ) -> User | None:
        """Asigna técnico al incidente si ambos existen y el usuario es técnico activo."""
        db = _get_session()
        try:
            try:
                tech_uuid = UUID(technician_id)
                inc_uuid = UUID(incident_id)
            except ValueError:
                return None

            incident = db.scalar(
                select(IncidentModel).where(IncidentModel.id == inc_uuid)
            )
            if incident is None:
                return None

            tech = db.scalar(
                _technician_user_stmt().where(
                    UserModel.id == tech_uuid,
                    UserModel.is_active.is_(True),
                )
            )
            if tech is None:
                return None

            incident.technician_id = tech_uuid
            incident.updated_at = datetime.now(UTC)
            db.commit()
            db.refresh(tech)
            return _user_model_to_entity(tech)
        finally:
            db.close()

    def technician_available_list_all(self) -> list[User]:
        """Técnicos activos sin incidentes en estado Nuevo o En_proceso asignados."""
        db = _get_session()
        try:
            busy = exists().where(
                IncidentModel.technician_id == UserModel.id,
                IncidentModel.status.in_(
                    (IncidentStatus.NUEVO.value, IncidentStatus.EN_PROCESO.value)
                ),
            )
            stmt = (
                _technician_user_stmt()
                .where(UserModel.is_active.is_(True))
                .where(~busy)
                .order_by(UserModel.last_name, UserModel.first_name)
            )
            rows = db.scalars(stmt).all()
            return [_user_model_to_entity(r) for r in rows]
        finally:
            db.close()
