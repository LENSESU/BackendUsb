"""Rutas HTTP para Incidentes. Requieren JWT y rol autorizado."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user_id, require_role
from app.api.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from app.application.ports import IncidentRepositoryPort
from app.application.services import IncidentService
from app.core.exceptions import NotFoundError
from app.domain.entities.incident import Incident

router = APIRouter()

_repository: IncidentRepositoryPort | None = None


def get_incident_service() -> IncidentService:
    """Obtiene el servicio de Incidentes (DI: SQL repository)."""
    global _repository
    from app.infrastructure.adapters.sql_incident_repository import (
        SqlIncidentRepository,
    )

    if _repository is None:
        _repository = SqlIncidentRepository()
    return IncidentService(repository=_repository)


def _incident_to_response(incident: Incident) -> IncidentResponse:
    """Mapea entidad de dominio a schema de respuesta."""
    assert incident.id is not None and incident.created_at is not None
    loc = incident.location
    return IncidentResponse(
        id=incident.id,
        student_id=incident.student_id,
        technician_id=incident.technician_id,
        category_id=incident.category_id,
        description=incident.description,
        campus_place=loc.campus_place if loc else None,
        latitude=loc.latitude if loc else None,
        longitude=loc.longitude if loc else None,
        status=incident.status,
        priority=incident.priority,
        before_photo_id=incident.before_photo_id,
        after_photo_id=incident.after_photo_id,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def create_incident(
    payload: IncidentCreate,
    current_user_id: UUID = Depends(get_current_user_id),
) -> IncidentResponse:
    """Crea un nuevo incidente. student_id se asigna desde el JWT."""
    service = get_incident_service()
    incident = service.create_incident(
        student_id=current_user_id,
        category_id=payload.category_id,
        description=payload.description,
        before_photo_id=payload.before_photo_id,
        campus_place=payload.campus_place,
        latitude=payload.latitude,
        longitude=payload.longitude,
        priority=payload.priority,
    )
    return _incident_to_response(incident)


@router.get(
    "/",
    response_model=list[IncidentResponse],
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_incidents() -> list[IncidentResponse]:
    """Lista todos los incidentes."""
    service = get_incident_service()
    incidents = service.list_incidents()
    return [_incident_to_response(i) for i in incidents]


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_incident(incident_id: UUID) -> IncidentResponse:
    """Obtiene un incidente por ID."""
    service = get_incident_service()
    incident = service.get_incident(incident_id)
    if incident is None:
        raise NotFoundError("Incidente no encontrado")
    return _incident_to_response(incident)


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[Depends(require_role("Administrator", "Technician"))],
)
def update_incident(incident_id: UUID, payload: IncidentUpdate) -> IncidentResponse:
    """Actualiza estado o prioridad (y otros campos) de un incidente."""
    service = get_incident_service()
    incident = service.update_incident(
        incident_id,
        technician_id=payload.technician_id,
        category_id=payload.category_id,
        description=payload.description,
        campus_place=payload.campus_place,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=payload.status,
        priority=payload.priority,
        after_photo_id=payload.after_photo_id,
    )
    if incident is None:
        raise NotFoundError("Incidente no encontrado")
    return _incident_to_response(incident)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator", "Technician"))],
)
def delete_incident(incident_id: UUID) -> None:
    """Elimina un incidente. Solo Administrator o Technician."""
    service = get_incident_service()
    if service.get_incident(incident_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado",
        )
    service.delete_incident(incident_id)
    return None
