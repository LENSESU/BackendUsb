"""Adaptador SQLAlchemy que implementa IncidentRepositoryPort."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.core.config import settings
from app.domain.entities.incident import Incident, IncidentLocation
from app.infrastructure.database.models import IncidentModel


def _get_session() -> Session:
    """Crea una sesión síncrona contra la base de datos."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _to_entity(model: IncidentModel) -> Incident:
    """Convierte IncidentModel → entidad de dominio Incident."""
    location: IncidentLocation | None = None
    if (
        model.campus_place is not None
        or model.latitude is not None
        or model.longitude is not None
    ):
        lat = float(model.latitude) if model.latitude is not None else None
        lon = float(model.longitude) if model.longitude is not None else None
        location = IncidentLocation(
            campus_place=model.campus_place,
            latitude=lat,
            longitude=lon,
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


class SqlIncidentRepository(IncidentRepositoryPort):
    """Implementación del puerto de incidentes usando SQLAlchemy síncrono."""

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un incidente por su ID, o None si no existe."""
        db = _get_session()
        try:
            stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
            model = db.scalar(stmt)
            return _to_entity(model) if model else None
        finally:
            db.close()

    def set_after_photo_id(self, incident_id: UUID, file_id: UUID) -> None:
        """Asocia la foto 'después' (evidencia) al incidente y actualiza updated_at."""
        db = _get_session()
        try:
            stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
            model = db.scalar(stmt)
            if model is None:
                return
            model.after_photo_id = file_id
            model.updated_at = datetime.now(UTC)
            db.commit()
        finally:
            db.close()
