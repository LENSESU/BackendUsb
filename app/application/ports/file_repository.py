"""Puerto (interfaz) para persistencia de archivos (FileResource)."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.file_resource import FileResource


class FileRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de archivos."""

    @abstractmethod
    def create(self, file: FileResource) -> FileResource:
        """Persiste un nuevo archivo y retorna la entidad con id asignado."""
        ...

    @abstractmethod
    def get_by_id(self, file_id: UUID) -> FileResource | None:
        """Obtiene un archivo por su ID, o None si no existe."""
        ...
