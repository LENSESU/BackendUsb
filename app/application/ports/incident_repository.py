"""Puerto (interfaz) para persistencia de Incidents. Lo implementa la infraestructura."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Incident


class IncidentRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Incidents."""

    @abstractmethod
    def list_all(self) -> list[Incident]:
        """Lista todos los incidentes."""
        ...

    @abstractmethod
    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un Incident por su ID."""
        ...

    @abstractmethod
    def save(self, incident: Incident) -> Incident:
        """Guarda o actualiza un Incident."""
        ...
