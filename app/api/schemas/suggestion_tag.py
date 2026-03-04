"""Esquemas Pydantic para la relación sugerencia-etiqueta."""

from pydantic import BaseModel, Field


class SuggestionTagCreate(BaseModel):
    """Payload para asociar una etiqueta a una sugerencia."""

    suggestion_id: int = Field(..., ge=1)
    tag_id: int = Field(..., ge=1)


class SuggestionTagResponse(BaseModel):
    """Respuesta con datos de la relación sugerencia-etiqueta."""

    suggestion_id: int
    tag_id: int

    model_config = {"from_attributes": True}

