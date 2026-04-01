"""Rutas HTTP para categorías de incidentes.

- GET  /  lista todas las categorías (cualquier rol autenticado)
- POST /  crea una nueva categoría (solo Administrator)
- PATCH /{category_id} actualiza una categoría (solo Administrator)
- DELETE /{category_id} elimina una categoría (solo Administrator)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.auth import require_role
from app.api.dependencies.incident_category import get_incident_category_service
from app.api.schemas.incident_category import (
    IncidentCategoryCreate,
    IncidentCategoryListResponse,
    IncidentCategoryResponse,
    IncidentCategoryUpdate,
)
from app.application.services.incident_category_service import IncidentCategoryService

router = APIRouter()


@router.get(
    "/",
    response_model=IncidentCategoryListResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_categories(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    service: IncidentCategoryService = Depends(get_incident_category_service),
) -> IncidentCategoryListResponse:
    """Lista todas las categorías registradas."""
    all_categories = [
        IncidentCategoryResponse.model_validate(c) for c in service.list_all()
    ]
    total = len(all_categories)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    return IncidentCategoryListResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=all_categories[start:end],
    )


@router.get(
    "/{category_id}",
    response_model=IncidentCategoryResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_category(
    category_id: str,
    service: IncidentCategoryService = Depends(get_incident_category_service),
) -> IncidentCategoryResponse:
    """Retorna una categoría por su ID."""
    category = service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"Categoría con id {category_id} no encontrada",
                "error_code": "INCIDENT_CATEGORY_NOT_FOUND",
            },
        )
    return IncidentCategoryResponse.model_validate(category)


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
            detail={
                "message": str(e),
                "error_code": "INCIDENT_CATEGORY_ALREADY_EXISTS",
            },
        ) from e
    return IncidentCategoryResponse.model_validate(category)


@router.patch(
    "/{category_id}",
    response_model=IncidentCategoryResponse,
    dependencies=[Depends(require_role("Administrator"))],
)
def update_category(
    category_id: str,
    payload: IncidentCategoryUpdate,
    service: IncidentCategoryService = Depends(get_incident_category_service),
) -> IncidentCategoryResponse:
    """Actualiza una categoría existente. Solo Administrators."""
    try:
        category = service.update(
            category_id=category_id,
            name=payload.name,
            description=payload.description,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": str(e),
                "error_code": "INCIDENT_CATEGORY_ALREADY_EXISTS",
            },
        ) from e
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"Categoría con id {category_id} no encontrada",
                "error_code": "INCIDENT_CATEGORY_NOT_FOUND",
            },
        )
    return IncidentCategoryResponse.model_validate(category)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator"))],
)
def delete_category(
    category_id: str,
    service: IncidentCategoryService = Depends(get_incident_category_service),
) -> None:
    """Elimina una categoría existente. Solo Administrators."""
    deleted = service.delete(category_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"Categoría con id {category_id} no encontrada",
                "error_code": "INCIDENT_CATEGORY_NOT_FOUND",
            },
        )
