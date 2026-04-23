"""Caso de uso: carga de evidencias de incidentes."""

from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from google.api_core.exceptions import GoogleAPIError

from app.application.ports.file_repository import FileRepositoryPort
from app.application.ports.file_storage import FileStoragePort, StoredFileResult
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.file_validation_service import FileValidationService
from app.domain.entities.incident import EvidencePhotoType, IncidentStatus


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
        photo_type: EvidencePhotoType = EvidencePhotoType.BEFORE,
    ) -> StoredFileResult:
        # Validaciones previas al cargue cuando se trata de la foto final (HU-E5-028)
        if photo_type == EvidencePhotoType.AFTER:
            existing = self._incident_repository.get_by_id(incident_id)
            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": (
                            "No se encontró el incidente para asociar la evidencia."
                        ),
                        "error_code": "INCIDENT_NOT_FOUND",
                    },
                )
            if existing.status not in (
                IncidentStatus.EN_PROCESO.value,
                IncidentStatus.RESUELTO.value,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": (
                            "Solo se puede subir la foto de evidencia final cuando el "
                            "incidente está en proceso o resuelto."
                        ),
                        "error_code": "INCIDENT_AFTER_PHOTO_INVALID_STATE",
                    },
                )

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

        # Asociar el archivo al campo correspondiente según el tipo.
        incident = self._incident_repository.get_by_id(incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el incidente para asociar la evidencia.",
            )

        if photo_type == EvidencePhotoType.AFTER:
            incident.after_photo_id = file_id
        else:
            incident.before_photo_id = file_id
        self._incident_repository.save(incident)

        return stored_file
