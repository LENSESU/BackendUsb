"""Adaptador en memoria para FileRepositoryPort (tests y desarrollo sin BD)."""

from uuid import UUID, uuid4

from app.application.ports.file_repository import FileRepositoryPort
from app.domain.entities.file_resource import FileResource


class InMemoryFileRepository(FileRepositoryPort):
    """Almacena archivos en un diccionario en memoria."""

    def __init__(self) -> None:
        self._store: dict[UUID, FileResource] = {}

    def create(self, file: FileResource) -> FileResource:
        """Guarda el archivo en memoria y retorna la entidad con id asignado."""
        new_id = uuid4()
        persisted = FileResource(
            id=new_id,
            url=file.url,
            file_type=file.file_type,
            uploaded_by_user_id=file.uploaded_by_user_id,
            created_at=file.created_at,
        )
        self._store[new_id] = persisted
        return persisted

    def get_by_id(self, file_id: UUID) -> FileResource | None:
        """Obtiene un archivo por su ID, o None si no existe."""
        return self._store.get(file_id)
