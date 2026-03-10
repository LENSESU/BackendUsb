"""Rutas HTTP para categorías de incidentes.

- GET  /  lista todas las categorías (cualquier rol autenticado)
- POST /  crea una nueva categoría (solo Administrator)
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_role
from app.api.dependencies.incident_category import get_incident_category_service
from app.api.schemas.incident_category import (
    IncidentCategoryCreate,
    IncidentCategoryListResponse,
    IncidentCategoryResponse,
)
from app.application.services.incident_category_service import IncidentCategoryService

router = APIRouter()


@router.get(
    "/",
    response_model=IncidentCategoryListResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_categories(
    service: IncidentCategoryService = Depends(get_incident_category_service),
) -> IncidentCategoryListResponse:
    """Lista todas las categorías registradas."""
    categories = [IncidentCategoryResponse.model_validate(c) for c in service.list_all()]
    return IncidentCategoryListResponse(count=len(categories), items=categories)


@router.post(
    "/",
    response_model=IncidentCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator"))],
)
def create_category(
    payload: IncidentCategoryCreate,
    service: IncidentCategoryService = Depends(get_incident_category_service),
) -> IncidentCategoryResponse:
    """Crea una nueva categoría. Solo Administrators."""
    try:
        category = service.create(name=payload.name, description=payload.description)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return IncidentCategoryResponse.model_validate(category)
