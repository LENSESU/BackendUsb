"""Rutas HTTP para Incidentes (HU-E2-011).

Creado para las tareas:
- #107 — Metadatos automáticos (student_id del JWT, created_at).
- #108 — Responder HTTP 201 Created en creación exitosa.
- #109 — (las pruebas validan este endpoint).

El endpoint de creación:
  - Requiere autenticación (JWT válido con rol Student, Administrator o Technician).
  - Inyecta ``student_id`` desde el token del usuario autenticado.
  - Fija ``created_at`` en el servidor (no acepta valor del cliente).
  - Retorna HTTP 201 con los datos del incidente creado.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import (
    get_current_user_id,
    require_role,
)
from app.api.schemas.incident import IncidentCreate, IncidentResponse
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_service import IncidentService

router = APIRouter()

# Repositorio in-memory (mismo patrón que Items)
_repository: IncidentRepositoryPort | None = None


def get_incident_service() -> IncidentService:
    """Obtiene el servicio de Incidentes.

    Usa un singleton in-memory por defecto (mismo patrón que Items).
    En producción se reemplazaría por un contenedor de DI con SQLAlchemy.
    """
    global _repository
    if _repository is None:
        from app.infrastructure.adapters.in_memory_incident_repository import (
            InMemoryIncidentRepository,
        )

        _repository = InMemoryIncidentRepository()
    return IncidentService(_repository)


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_role("Administrator", "Student", "Technician"))
    ],
)
def create_incident(
    payload: IncidentCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    """Crea un incidente con metadatos automáticos.

    #107: ``student_id`` se toma del JWT (no del payload).
           ``created_at`` se asigna en el servidor.
    #108: Responde 201 Created.
    """
    incident = service.create_incident(
        student_id=user_id,
        category_id=payload.category_id,
        description=payload.description,
        before_photo_id=payload.before_photo_id,
        priority=payload.priority,
        campus_place=payload.campus_place,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    return IncidentResponse(
        id=incident.id,
        student_id=incident.student_id,
        technician_id=incident.technician_id,
        category_id=incident.category_id,
        description=incident.description,
        campus_place=incident.location.campus_place if incident.location else None,
        latitude=incident.location.latitude if incident.location else None,
        longitude=incident.location.longitude if incident.location else None,
        status=incident.status,
        priority=incident.priority,
        before_photo_id=incident.before_photo_id,
        after_photo_id=incident.after_photo_id,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


@router.get(
    "/",
    response_model=list[IncidentResponse],
    dependencies=[
        Depends(require_role("Administrator", "Student", "Technician"))
    ],
)
def list_incidents(
    service: IncidentService = Depends(get_incident_service),
) -> list[IncidentResponse]:
    """Lista todos los incidentes."""
    incidents = service.list_incidents()
    return [
        IncidentResponse(
            id=inc.id,
            student_id=inc.student_id,
            technician_id=inc.technician_id,
            category_id=inc.category_id,
            description=inc.description,
            campus_place=inc.location.campus_place if inc.location else None,
            latitude=inc.location.latitude if inc.location else None,
            longitude=inc.location.longitude if inc.location else None,
            status=inc.status,
            priority=inc.priority,
            before_photo_id=inc.before_photo_id,
            after_photo_id=inc.after_photo_id,
            created_at=inc.created_at,
            updated_at=inc.updated_at,
        )
        for inc in incidents
    ]


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[
        Depends(require_role("Administrator", "Student", "Technician"))
    ],
)
def get_incident(
    incident_id: UUID,
    service: IncidentService = Depends(get_incident_service),
) -> IncidentResponse:
    """Obtiene un incidente por ID."""
    incident = service.get_incident(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidente no encontrado",
        )
    return IncidentResponse(
        id=incident.id,
        student_id=incident.student_id,
        technician_id=incident.technician_id,
        category_id=incident.category_id,
        description=incident.description,
        campus_place=incident.location.campus_place if incident.location else None,
        latitude=incident.location.latitude if incident.location else None,
        longitude=incident.location.longitude if incident.location else None,
        status=incident.status,
        priority=incident.priority,
        before_photo_id=incident.before_photo_id,
        after_photo_id=incident.after_photo_id,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )
