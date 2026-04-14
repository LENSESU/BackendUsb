"""Adaptador SQLAlchemy que implementa IncidentRepositoryPort."""

from abc import abstractmethod
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.core.config import settings
from app.domain.entities.incident import Incident, IncidentLocation
from app.infrastructure.database.models import IncidentModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _model_to_entity(model: IncidentModel) -> Incident:
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
            stmt = select(IncidentModel).order_by(IncidentModel.created_at.desc())
            rows = db.scalars(stmt).all()
            return [_model_to_entity(m) for m in rows]
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

    @abstractmethod
    def update_status(self, incident_id: UUID, new_status: str) -> Incident | None:

        db = _get_session()
        try:
            stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
            model = db.scalar(stmt)
            if model is None:
                return None
            model.status = new_status
            model.updated_at = datetime.now(UTC)
            db.commit()
            db.refresh(model)
            return _model_to_entity(model)
        finally:
            db.close()
