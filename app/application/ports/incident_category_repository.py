from abc import ABC, abstractmethod

from app.domain.entities.incident_category import IncidentCategory


class IncidentCategoryRepositoryPort(ABC):
    @abstractmethod
    def save(self, category: IncidentCategory) -> IncidentCategory:
        """Persiste una nueva categoría."""
        ...

    @abstractmethod
    def find_by_name(self, name: str) -> IncidentCategory | None:
        """Retorna una categoría por nombre, o None si no existe."""
        ...

    @abstractmethod
    def find_all(self) -> list[IncidentCategory]:
        """Retorna todas las categorías registradas."""
        ...
