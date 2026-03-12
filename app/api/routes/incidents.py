"""Rutas HTTP para incidentes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies.storage import get_incident_evidence_service
from app.api.schemas import IncidentEvidenceUploadResponse
from app.application.services.incident_evidence_service import IncidentEvidenceService

router = APIRouter()


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
