from app.application.services.incident_category_service import IncidentCategoryService
from app.infrastructure.adapters.incident_category_repository import (
    SqlIncidentCategoryRepository,
)

_repo = SqlIncidentCategoryRepository()


def get_incident_category_service() -> IncidentCategoryService:
    return IncidentCategoryService(repository=_repo)
