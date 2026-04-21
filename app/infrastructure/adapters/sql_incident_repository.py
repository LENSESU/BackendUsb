"""Adaptador SQLAlchemy que implementa IncidentRepositoryPort."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.domain.entities.incident import Incident, IncidentLocation
from app.infrastructure.database.models import IncidentModel, UserModel
from app.infrastructure.db import SyncSessionLocal


def _get_session() -> Session:
    return SyncSessionLocal()


def _model_to_entity(
    model: IncidentModel,
    reporter_email: str | None = None,
    assigned_by_admin_name: str | None = None,
) -> Incident:
    """Convierte IncidentModel a entidad de dominio Incident."""
    location = None
    if (
        model.campus_place is not None
        or model.latitude is not None
        or model.longitude is not None
    ):
        location = IncidentLocation(
            campus_place=model.campus_place,
            latitude=float(model.latitude) if model.latitude is not None else None,
            longitude=float(model.longitude) if model.longitude is not None else None,
        )
    return Incident(
        id=model.id,
        student_id=model.student_id,
        technician_id=model.technician_id,
        category_id=model.category_id,
        description=model.description,
        status=model.status,
        priority=model.priority,
        before_photo_id=model.before_photo_id,
        after_photo_id=model.after_photo_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        location=location,
        reporter_email=reporter_email,
        assigned_by_admin_id=model.assigned_by_admin_id,
        assigned_by_admin_name=assigned_by_admin_name,
    )


def _entity_to_model(
    incident: Incident, existing: IncidentModel | None = None
) -> IncidentModel:
    """Crea o actualiza IncidentModel desde entidad."""
    loc = incident.location
    campus_place = loc.campus_place if loc else None
    latitude = loc.latitude if loc else None
    longitude = loc.longitude if loc else None

    if existing is not None:
        existing.student_id = incident.student_id
        existing.technician_id = incident.technician_id
        existing.assigned_by_admin_id = incident.assigned_by_admin_id
        existing.category_id = incident.category_id
        existing.description = incident.description
        existing.campus_place = campus_place
        existing.latitude = latitude
        existing.longitude = longitude
        existing.status = incident.status
        existing.priority = incident.priority
        existing.before_photo_id = incident.before_photo_id
        existing.after_photo_id = incident.after_photo_id
        existing.updated_at = datetime.now(UTC)
        return existing

    return IncidentModel(
        id=incident.id,
        student_id=incident.student_id,
        technician_id=incident.technician_id,
        assigned_by_admin_id=incident.assigned_by_admin_id,
        category_id=incident.category_id,
        description=incident.description,
        campus_place=campus_place,
        latitude=latitude,
        longitude=longitude,
        status=incident.status,
        priority=incident.priority,
        before_photo_id=incident.before_photo_id,
        after_photo_id=incident.after_photo_id,
    )


class SqlIncidentRepository(IncidentRepositoryPort):
    """Implementación del puerto de Incidentes usando SQLAlchemy síncrono."""

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        db = _get_session()
        try:
            stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
            model = db.scalar(stmt)
            return _model_to_entity(model) if model else None
        finally:
            db.close()

    def list_all(self) -> list[Incident]:
        db = _get_session()
        try:
            reporter_user = aliased(UserModel)
            assigner_user = aliased(UserModel)
            stmt = (
                select(
                    IncidentModel,
                    reporter_user.email,
                    assigner_user.first_name,
                    assigner_user.last_name,
                )
                .outerjoin(reporter_user, IncidentModel.student_id == reporter_user.id)
                .outerjoin(
                    assigner_user,
                    IncidentModel.assigned_by_admin_id == assigner_user.id,
                )
                .order_by(IncidentModel.created_at.desc())
            )
            rows = db.execute(stmt).all()
            incidents: list[Incident] = []
            for incident_model, reporter_email, assigner_first, assigner_last in rows:
                assigner_name = None
                if assigner_first or assigner_last:
                    assigner_name = " ".join(
                        p for p in (assigner_first, assigner_last) if p
                    )
                incidents.append(
                    _model_to_entity(
                        incident_model,
                        reporter_email,
                        assigner_name,
                    )
                )
            return incidents
        finally:
            db.close()

    def save(self, incident: Incident) -> Incident:
        db = _get_session()
        try:
            stmt = select(IncidentModel).where(IncidentModel.id == incident.id)
            existing = db.scalar(stmt)
            if existing:
                _entity_to_model(incident, existing)
                db.commit()
                db.refresh(existing)
                return _model_to_entity(existing)
            model = _entity_to_model(incident, None)
            db.add(model)
            db.commit()
            db.refresh(model)
            return _model_to_entity(model)
        finally:
            db.close()

    def delete(self, incident_id: UUID) -> bool:
        db = _get_session()
        try:
            stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
            model = db.scalar(stmt)
            if model is None:
                return False
            db.delete(model)
            db.commit()
            return True
        finally:
            db.close()
