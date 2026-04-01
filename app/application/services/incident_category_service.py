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

    def update(
        self,
        category_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> IncidentCategory | None:
        existing = self._repository.find_by_id(category_id)
        if existing is None:
            return None

        new_name = name.strip() if name is not None else existing.name
        if new_name != existing.name:
            duplicate = self._repository.find_by_name(new_name)
            if duplicate is not None and duplicate.id != existing.id:
                raise ValueError(f"Ya existe una categoría con el nombre '{new_name}'")

        updated = IncidentCategory(
            id=existing.id,
            name=new_name,
            description=description
            if description is not None
            else existing.description,
        )
        return self._repository.update(updated)

    def delete(self, category_id: str) -> bool:
        return self._repository.delete(category_id)
