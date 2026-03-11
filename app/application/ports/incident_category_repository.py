"""Puerto: contrato para el repositorio de categorías de incidentes."""
from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.incident_category import IncidentCategory


class IncidentCategoryRepository(ABC):

    @abstractmethod
    def get_all(self) -> list[IncidentCategory]:
        """Retorna todas las categorías disponibles."""
        ...

    @abstractmethod
    def get_by_id(self, category_id: UUID) -> IncidentCategory | None:
        """Retorna una categoría por su ID, o None si no existe."""
        ...