"""Puerto (interfaz) para persistencia de archivos subidos."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass
class FileData:
    """Datos de un archivo."""
    id: UUID
    url: str
    file_type: str | None
    uploaded_by_user_id: UUID | None


class FileRepositoryPort(ABC):
    """Contrato para persistir metadatos de archivos en la base de datos."""

    @abstractmethod
    def create_file(
        self,
        *,
        url: str,
        file_type: str | None,
        uploaded_by_user_id: UUID | None,
    ) -> UUID:
        """Crea un registro de archivo y retorna su ID."""
        ...

    @abstractmethod
    def get_by_id(self, file_id: UUID) -> FileData | None:
        """Obtiene un archivo por su ID."""
        ...
