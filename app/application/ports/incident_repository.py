"""Puerto (interfaz) para persistencia de Incidentes.

Creado para #107/#108/#109 (HU-E2-011 Crear Incidente).
Sigue el mismo patrón que ``ItemRepositoryPort``.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.incident import Incident


class IncidentRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Incidentes.

    Define las operaciones mínimas requeridas por ``IncidentService``.
    Implementaciones concretas:
      - ``InMemoryIncidentRepository`` (tests / desarrollo sin BD).
      - (futuro) adaptador SQLAlchemy para PostgreSQL en producción.
    """

    @abstractmethod
    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un Incidente por su ID.

        Args:
            incident_id: UUID del incidente a buscar.

        Returns:
            La entidad ``Incident`` si existe, ``None`` en caso contrario.
        """
        ...

    @abstractmethod
    def list_all(self) -> list[Incident]:
        """Lista todos los Incidentes registrados.

        Returns:
            Lista de entidades ``Incident``.  Vacía si no hay registros.
        """
        ...

    @abstractmethod
    def save(self, incident: Incident) -> Incident:
        """Persiste un Incidente nuevo.

        Args:
            incident: Entidad de dominio ya construida con metadatos automáticos.

        Returns:
            La misma entidad persistida (con ID asignado).
        """
        ...
