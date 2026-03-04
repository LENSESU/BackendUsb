"""Esquemas Pydantic para categorías de incidentes."""

from pydantic import BaseModel, Field


class IncidentCategoryCreate(BaseModel):
    """Payload para crear una categoría de incidente."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)


class IncidentCategoryResponse(BaseModel):
    """Respuesta con datos de una categoría de incidente."""

    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
