"""Puerto (interfaz) para persistencia de Incidentes."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.domain.entities.incident import Incident


class IncidentRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Incidentes."""

    @abstractmethod
    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un Incidente por su ID."""
        ...

    @abstractmethod
    def list_all(
        self,
        *,
        status: str | None = None,
        category_id: UUID | None = None,
        priority: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Incident]:
        """Lista incidentes con filtros opcionales por estado, categoría,
        prioridad y rango de fechas."""
        ...

    @abstractmethod
    def save(self, incident: Incident) -> Incident:
        """Guarda o actualiza un incidente."""
        ...

    @abstractmethod
    def delete(self, incident_id: UUID) -> bool:
        """Elimina un incidente por ID. Retorna True si existía."""
        ...
