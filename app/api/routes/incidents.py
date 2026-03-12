"""Rutas HTTP para incidentes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies.auth import get_current_user_id, require_role
from app.api.dependencies.storage import get_incident_evidence_service
from app.api.schemas import (
    IncidentCreate,
    IncidentEvidenceUploadResponse,
    IncidentResponse,
)
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.application.services.incident_service import IncidentService
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)

router = APIRouter()


_repository: IncidentRepositoryPort | None = None


def get_incident_service() -> IncidentService:
    """Obtiene el servicio de incidentes utilizando un repositorio in-memory.

    Este patrón evita depender de la base de datos real durante las pruebas
    del endpoint, similar a como se hace con Items.
    """
    global _repository

    if _repository is None:
        _repository = InMemoryIncidentRepository()
    return IncidentService(repository=_repository)


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=201,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def create_incident(
    payload: IncidentCreate,
    current_user_id: UUID = Depends(get_current_user_id),
) -> IncidentResponse:
    """Crea un incidente usando el usuario autenticado como student_id."""
    service = get_incident_service()

    now = datetime.now(UTC)
    incident = service.create_incident(
        student_id=current_user_id,
        category_id=payload.categoria_id,
        description=payload.descripcion,
        before_photo_id=payload.foto_antes_id,
        campus_place=payload.lugar_campus,
        latitude=payload.latitud,
        longitude=payload.longitud,
        priority=payload.prioridad,
        status=payload.estado,
    )
    incident.created_at = now

    return IncidentResponse.model_validate(incident)


@router.post(
    "/{incident_id}/evidence",
    response_model=IncidentEvidenceUploadResponse,
    status_code=201,
)
async def upload_incident_evidence(
    incident_id: UUID,
    photo: UploadFile = File(...),
    evidence_service: IncidentEvidenceService = Depends(get_incident_evidence_service),
) -> IncidentEvidenceUploadResponse:
    """Valida y carga una evidencia fotográfica para un incidente."""
    stored_file = await evidence_service.upload_evidence(
        incident_id=incident_id,
        file=photo,
    )

    return IncidentEvidenceUploadResponse(
        incident_id=incident_id,
        filename=photo.filename or "",
        content_type=(photo.content_type or "").lower(),
        storage_object_name=stored_file.object_name,
        file_url=stored_file.file_url,
        message="Evidencia fotográfica cargada correctamente",
    )
