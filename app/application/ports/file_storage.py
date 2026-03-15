from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


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
