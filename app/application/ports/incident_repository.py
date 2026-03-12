"""Puerto (interfaz) para persistencia de incidentes."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.incident import Incident


class IncidentRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de incidentes."""

    @abstractmethod
    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un incidente por su ID, o None si no existe."""
        ...

    @abstractmethod
    def set_after_photo_id(self, incident_id: UUID, file_id: UUID) -> None:
        """Asocia la foto 'después' (evidencia) al incidente. Actualiza updated_at."""
        ...
