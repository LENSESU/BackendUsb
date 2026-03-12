"""Rutas HTTP para Incidentes. Requieren JWT y rol autorizado."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_current_user_id, require_role
from app.api.schemas.incident import (
    Campus,
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
    selected: list[Campus] | None = None
    if loc and loc.campus_place:
        try:
            selected = [Campus(loc.campus_place)]
        except ValueError:
            selected = [Campus.OTRO]
    return IncidentResponse(
        id=incident.id,
        estudiante_id=incident.student_id,
        tecnico_id=incident.technician_id,
        categoria_id=incident.category_id,
        descripcion=incident.description,
        lugar_campus=selected,
        latitud=float(loc.latitude) if loc and loc.latitude is not None else None,
        longitud=float(loc.longitude) if loc and loc.longitude is not None else None,
        estado=incident.status,
        prioridad=incident.priority,
        foto_antes_id=incident.before_photo_id,
        foto_despues_id=incident.after_photo_id,
        creado_en=incident.created_at,
        actualizado_en=incident.updated_at,
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
    """Crea un nuevo incidente. El estudiante se asigna desde el JWT."""
    service = get_incident_service()
    campus_name = (
        payload.lugar_campus[0].value
        if payload.lugar_campus and len(payload.lugar_campus) > 0
        else None
    )
    incident = service.create_incident(
        student_id=current_user_id,
        category_id=payload.categoria_id,
        description=payload.descripcion,
        before_photo_id=payload.foto_antes_id,
        campus_place=campus_name,
        latitude=payload.latitud,
        longitude=payload.longitud,
        priority=payload.prioridad,
        status=payload.estado,
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
    campus_name = (
        payload.lugar_campus[0].value
        if payload.lugar_campus and len(payload.lugar_campus) > 0
        else None
    )
    incident = service.update_incident(
        incident_id,
        technician_id=payload.tecnico_id,
        category_id=payload.categoria_id,
        description=payload.descripcion,
        campus_place=campus_name,
        latitude=payload.latitud,
        longitude=payload.longitud,
        status=payload.estado,
        priority=payload.prioridad,
        before_photo_id=payload.foto_antes_id,
        after_photo_id=payload.foto_despues_id,
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
