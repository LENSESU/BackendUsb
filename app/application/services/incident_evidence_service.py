"""Caso de uso: carga de evidencias de incidentes."""

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from app.application.ports.file_repository import FileRepositoryPort
from app.application.ports.file_storage import (
    FileStoragePort,
    StorageUploadError,
    StoredFileResult,
)
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.file_validation_service import FileValidationService
from app.domain.entities.file_resource import FileResource


@dataclass(frozen=True)
class UploadEvidenceResult:
    """Resultado: subida a storage + registro en BD + vínculo al incidente."""

    stored_file: StoredFileResult
    file_id: UUID


class IncidentEvidenceService:
    """Orquesta validación, storage externo (GCS) y persistencia en BD."""

    def __init__(
        self,
        storage: FileStoragePort,
        file_repository: FileRepositoryPort,
        incident_repository: IncidentRepositoryPort,
    ) -> None:
        self._storage = storage
        self._file_repository = file_repository
        self._incident_repository = incident_repository

    async def upload_evidence(
        self,
        *,
        incident_id: UUID,
        file: UploadFile,
    ) -> UploadEvidenceResult:
        """Valida el archivo, sube a GCS, guarda la URL en BD y la vincula al incidente.

        Lanza:
            HTTPException: 404 si el incidente no existe; 400 por validación;
            502 por fallo de GCS.
        """
        incident = self._incident_repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El incidente no existe.",
            )

        await FileValidationService.validate_incident_evidence_image(file)
        file_content = await file.read()
        content_type = (file.content_type or "application/octet-stream").lower()

        try:
            stored_file = await self._storage.upload_incident_evidence(
                incident_id=incident_id,
                filename=file.filename or "evidence.jpg",
                content_type=content_type,
                data=file_content,
            )
        except StorageUploadError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Error al subir la imagen al servicio de almacenamiento. "
                    "Intente nuevamente más tarde."
                ),
            ) from exc

        # Guardar en la base de datos la URL retornada por GCS
        file_url = stored_file.file_url or f"gs://placeholder/{stored_file.object_name}"
        file_resource = FileResource(
            id=None,
            url=file_url,
            file_type=content_type,
            uploaded_by_user_id=None,
        )
        persisted = self._file_repository.create(file_resource)
        assert persisted.id is not None

        # Vincular el archivo al incidente (foto "después")
        self._incident_repository.set_after_photo_id(incident_id, persisted.id)

        return UploadEvidenceResult(stored_file=stored_file, file_id=persisted.id)
