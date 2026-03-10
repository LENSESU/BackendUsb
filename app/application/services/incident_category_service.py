from app.application.ports.incident_category_repository import (
    IncidentCategoryRepositoryPort,
)
from app.domain.entities.incident_category import IncidentCategory


class IncidentCategoryService:
    """Casos de uso para gestión de categorías de incidentes."""

    def __init__(self, repository: IncidentCategoryRepositoryPort) -> None:
        self._repository = repository

    def create(self, name: str, description: str | None) -> IncidentCategory:
        if self._repository.find_by_name(name) is not None:
            raise ValueError(f"Ya existe una categoría con el nombre '{name}'")

        return self._repository.save(
            IncidentCategory(id=None, name=name, description=description)
        )

    def list_all(self) -> list[IncidentCategory]:
        return self._repository.find_all()
    
    def get_by_id(self, category_id: str) -> IncidentCategory | None:
        return self._repository.find_by_id(category_id)
