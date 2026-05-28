"""Adaptador SQLAlchemy para el puerto de técnicos (usuarios con rol Technician)."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.application.ports.technician_repository import TechnicianRepositoryPort
from app.domain.entities.incident import Incident, IncidentLocation, IncidentStatus
from app.domain.entities.user import User
from app.infrastructure.database.models import IncidentModel, RoleModel, UserModel
from app.infrastructure.db import SyncSessionLocal

TECHNICIAN_ROLE_NAME = "Technician"


def _get_session() -> Session:
    return SyncSessionLocal()


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


def _incident_model_to_entity(row: IncidentModel) -> Incident:
    return Incident(
        id=row.id,
        student_id=row.student_id,
        technician_id=row.technician_id,
        assigned_by_admin_id=row.assigned_by_admin_id,
        category_id=row.category_id,
        description=row.description,
        status=IncidentStatus(row.status),
        priority=row.priority,
        before_photo_id=row.before_photo_id,
        after_photo_id=row.after_photo_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        location=IncidentLocation(
            campus_place=row.campus_place,
            latitude=float(row.latitude) if row.latitude is not None else None,
            longitude=float(row.longitude) if row.longitude is not None else None,
        ),
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
        """Todos los técnicos, activos e inactivos, ordenados por apellido."""
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
        self,
        technician_id: str,
        incident_id: str,
        assigned_by_admin_id: str | None = None,
    ) -> User | None:
        """Asigna técnico al incidente si ambos existen y el usuario es
        técnico activo."""
        db = _get_session()
        try:
            try:
                tech_uuid = UUID(technician_id)
                inc_uuid = UUID(incident_id)
                admin_uuid = (
                    UUID(assigned_by_admin_id) if assigned_by_admin_id else None
                )
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
            incident.assigned_by_admin_id = admin_uuid
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

    # ------------------------------------------------------------------
    # Gestión admin
    # ------------------------------------------------------------------

    def create_technician(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
    ) -> User:
        """
        Crea un usuario con rol Technician.

        Raises:
            ValueError: Si el email ya está registrado.
        """
        db = _get_session()
        try:
            # Verificar email duplicado (en cualquier rol)
            existing = db.scalar(select(UserModel).where(UserModel.email == email))
            if existing is not None:
                raise ValueError(f"El email '{email}' ya está registrado.")

            # Obtener el role_id del rol Technician
            role = db.scalar(
                select(RoleModel).where(RoleModel.name == TECHNICIAN_ROLE_NAME)
            )
            if role is None:
                raise ValueError(
                    f"El rol '{TECHNICIAN_ROLE_NAME}' no existe en la base de datos."
                )

            new_user = UserModel(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
                role_id=role.id,
                is_active=True,
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return _user_model_to_entity(new_user)
        finally:
            db.close()

    def update_technician(
        self,
        user_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> User | None:
        """
        Actualiza solo los campos provistos (PATCH semántico).

        Raises:
            ValueError: Si el nuevo email ya pertenece a otro usuario.
        """
        db = _get_session()
        try:
            uid = UUID(user_id)
            row = db.scalar(_technician_user_stmt().where(UserModel.id == uid))
            if row is None:
                return None

            if email is not None and email != row.email:
                conflict = db.scalar(
                    select(UserModel).where(
                        UserModel.email == email,
                        UserModel.id != uid,
                    )
                )
                if conflict is not None:
                    raise ValueError(f"El email '{email}' ya pertenece a otro usuario.")
                row.email = email

            if first_name is not None:
                row.first_name = first_name
            if last_name is not None:
                row.last_name = last_name

            db.commit()
            db.refresh(row)
            return _user_model_to_entity(row)
        finally:
            db.close()

    def set_active_status(self, user_id: str, is_active: bool) -> User | None:
        """
        Activa o desactiva un técnico por su ID.

        Retorna None si el técnico no existe.
        """
        db = _get_session()
        try:
            uid = UUID(user_id)
            row = db.scalar(_technician_user_stmt().where(UserModel.id == uid))
            if row is None:
                return None

            row.is_active = is_active
            db.commit()
            db.refresh(row)
            return _user_model_to_entity(row)
        finally:
            db.close()

    def find_incidents_by_technician(self, user_id: str) -> list[Incident]:
        """
        Todos los incidentes asignados al técnico, más recientes primero.
        """
        db = _get_session()
        try:
            uid = UUID(user_id)
            stmt = (
                select(IncidentModel)
                .where(IncidentModel.technician_id == uid)
                .order_by(IncidentModel.created_at.desc())
            )
            rows = db.scalars(stmt).all()
            return [_incident_model_to_entity(r) for r in rows]
        finally:
            db.close()
