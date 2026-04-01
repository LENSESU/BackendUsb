"""Esquemas Pydantic para categorías de incidentes."""

from uuid import UUID

from pydantic import BaseModel, Field


class IncidentCategoryCreate(BaseModel):
    """Payload para crear una categoría de incidente."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)


class IncidentCategoryUpdate(BaseModel):
    """Payload para actualizar una categoría de incidente."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)


class IncidentCategoryResponse(BaseModel):
    """Respuesta con datos de una categoría de incidente."""

    id: UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class IncidentCategoryListResponse(BaseModel):
    """Respuesta paginada para listado de categorías."""

    page: int
    limit: int
    total: int
    total_pages: int
    items: list[IncidentCategoryResponse]
