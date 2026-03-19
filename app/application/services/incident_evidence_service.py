"""Caso de uso: carga de evidencias de incidentes."""

from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from google.api_core.exceptions import GoogleAPIError

from app.application.ports.file_repository import FileRepositoryPort
from app.application.ports.file_storage import FileStoragePort, StoredFileResult
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.file_validation_service import FileValidationService


class IncidentEvidenceService:
    """Orquesta validación de archivo, almacenamiento y asociación al incidente."""

    def __init__(
        self,
        *,
        storage: FileStoragePort,
        incident_repository: IncidentRepositoryPort,
        file_repository: FileRepositoryPort,
    ) -> None:
        self._storage = storage
        self._incident_repository = incident_repository
        self._file_repository = file_repository

    async def upload_evidence(
        self,
        *,
        incident_id: UUID,
        file: UploadFile,
    ) -> StoredFileResult:
        await FileValidationService.validate_incident_evidence_image(file)
        file_content = await file.read()

        try:
            stored_file = await self._storage.upload_incident_evidence(
                incident_id=incident_id,
                filename=file.filename or "evidence.jpg",
                content_type=(file.content_type or "application/octet-stream").lower(),
                data=file_content,
            )
        except GoogleAPIError as exc:
            # Error específico del proveedor de almacenamiento (por ejemplo, GCS).
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "No se pudo subir la evidencia al almacenamiento de Google Cloud. "
                    "Intente nuevamente más tarde."
                ),
            ) from exc
        except Exception as exc:  # noqa: BLE001
            # Error inesperado al subir la evidencia.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error inesperado al subir la evidencia.",
            ) from exc

        # Si el proveedor de almacenamiento no devuelve URL, no podemos crear FileModel.
        if stored_file.file_url is None:
            return stored_file

        # Crear registro en tabla files con la URL retornada por el almacenamiento.
        file_id = self._file_repository.create_file(
            url=stored_file.file_url,
            file_type=(file.content_type or "").lower(),
            uploaded_by_user_id=None,  # Enlazar al usuario autenticado en el futuro.
        )

        # Asociar el archivo como foto "antes" del incidente.
        incident = self._incident_repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el incidente para asociar la evidencia.",
            )

        incident.before_photo_id = file_id
        self._incident_repository.save(incident)

        return stored_file
