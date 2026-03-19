"""Puerto (interfaz) para persistencia de archivos subidos."""

from abc import ABC, abstractmethod
from uuid import UUID


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
