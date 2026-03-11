"""Servicio: lógica de negocio para categorías de incidentes."""
from uuid import UUID

from app.application.ports.incident_category_repository import (
    IncidentCategoryRepository,
)
from app.domain.entities.incident_category import IncidentCategory


class IncidentCategoryService:

    def __init__(self, repository: IncidentCategoryRepository) -> None:
        self._repository = repository

    def get_all_categories(self) -> list[IncidentCategory]:
        """Retorna todas las categorías disponibles."""
        return self._repository.get_all()

    def validate_category_id(self, category_id: UUID) -> IncidentCategory:
        """
        Valida que el category_id exista en la tabla maestra.
        Lanza ValueError si es None o no existe.
        """
        if category_id is None:
            raise ValueError("El category_id no puede ser nulo.")

        category = self._repository.get_by_id(category_id)

        if category is None:
            raise ValueError(f"La categoría con id '{category_id}' no existe.")

        return category