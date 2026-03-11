"""Caso de uso: carga de evidencias de incidentes."""

from uuid import UUID

from fastapi import UploadFile

from app.application.ports.file_storage import FileStoragePort, StoredFileResult
from app.application.services.file_validation_service import FileValidationService


class IncidentEvidenceService:
    """Orquesta validación de archivo y persistencia en almacenamiento externo."""

    def __init__(self, storage: FileStoragePort) -> None:
        self._storage = storage

    async def upload_evidence(
        self,
        *,
        incident_id: UUID,
        file: UploadFile,
    ) -> StoredFileResult:
        await FileValidationService.validate_incident_evidence_image(file)
        file_content = await file.read()

        return await self._storage.upload_incident_evidence(
            incident_id=incident_id,
            filename=file.filename or "evidence.jpg",
            content_type=(file.content_type or "application/octet-stream").lower(),
            data=file_content,
        )
