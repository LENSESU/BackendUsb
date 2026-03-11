"""Rutas: endpoints para categorías de incidentes."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.incident_category import IncidentCategoryResponse
from app.application.services.incident_category_service import IncidentCategoryService
from app.infrastructure.adapters.incident_category_repository import (
    SqlIncidentCategoryRepository,
)

router = APIRouter(prefix="/incident-categories", tags=["Incident Categories"])


def get_service() -> IncidentCategoryService:
    repo = SqlIncidentCategoryRepository()
    return IncidentCategoryService(repo)


@router.get("/", response_model=list[IncidentCategoryResponse])
def list_categories():
    """Retorna todas las categorías de incidentes disponibles."""
    return get_service().get_all_categories()


@router.get("/{category_id}", response_model=IncidentCategoryResponse)
def get_category(category_id: UUID):
    """Retorna una categoría por su ID. Lanza 404 si no existe."""
    try:
        return get_service().validate_category_id(category_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))