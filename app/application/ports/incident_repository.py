"""Puerto (interfaz) para persistencia de Incidentes."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.incident import Incident


class IncidentRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Incidentes."""

    @abstractmethod
    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un Incidente por su ID."""
        ...

    @abstractmethod
    def list_all(self) -> list[Incident]:
        """Lista todos los incidentes."""
        ...

    @abstractmethod
    def save(self, incident: Incident) -> Incident:
        """Guarda o actualiza un incidente."""
        ...

    @abstractmethod
    def delete(self, incident_id: UUID) -> bool:
        """Elimina un incidente por ID. Retorna True si existía."""
        ...
