from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


class StorageUploadError(Exception):
    """Excepción de dominio al subir archivos a storage externo (S3, GCS, etc.)."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


@dataclass(frozen=True)
class StoredFileResult:
    """Resultado de persistir un archivo en un proveedor externo."""

    object_name: str
    file_url: str | None = None


class FileStoragePort(ABC):
    """Puerto para almacenamiento de archivos de evidencia."""

    @abstractmethod
    async def upload_incident_evidence(
        self,
        *,
        incident_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        """Guarda una evidencia y retorna metadatos del archivo persistido."""
        ...
