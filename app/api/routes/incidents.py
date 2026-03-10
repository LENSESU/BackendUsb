"""Rutas HTTP para incidentes."""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.api.schemas import IncidentEvidenceUploadResponse
from app.application.services import FileValidationService

router = APIRouter()


@router.post(
    "/{incident_id}/evidence",
    response_model=IncidentEvidenceUploadResponse,
    status_code=201,
)
async def upload_incident_evidence(
    incident_id: UUID,
    photo: UploadFile = File(...),
) -> IncidentEvidenceUploadResponse:
    """Valida y acepta una evidencia fotográfica para un incidente."""
    await FileValidationService.validate_incident_evidence_image(photo)

    return IncidentEvidenceUploadResponse(
        incident_id=incident_id,
        filename=photo.filename or "",
        content_type=(photo.content_type or "").lower(),
        message="Evidencia fotográfica validada correctamente",
    )
