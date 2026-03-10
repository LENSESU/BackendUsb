from uuid import uuid4

from app.application.ports.incident_category_repository import (
    IncidentCategoryRepositoryPort,
)
from app.domain.entities.incident_category import IncidentCategory


class InMemoryIncidentCategoryRepository(IncidentCategoryRepositoryPort):
    """Adaptador en memoria para categorías de incidentes."""

    def __init__(self) -> None:
        self._store: dict = {}

    def save(self, category: IncidentCategory) -> IncidentCategory:
        new_category = IncidentCategory(
            id=uuid4(),
            name=category.name,
            description=category.description,
        )
        self._store[new_category.id] = new_category
        return new_category

    def find_by_name(self, name: str) -> IncidentCategory | None:
        return next(
            (c for c in self._store.values() if c.name.lower() == name.lower()),
            None,
        )

    def find_all(self) -> list[IncidentCategory]:
        return list(self._store.values())

    def find_by_id(self, category_id: str) -> IncidentCategory | None:
        for category in self._categories:
            if category.id == category_id:
                return category
        return None