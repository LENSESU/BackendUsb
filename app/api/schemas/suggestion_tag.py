"""Esquemas Pydantic para la relación sugerencia-etiqueta."""

from uuid import UUID

from pydantic import BaseModel, Field


class SuggestionTagCreate(BaseModel):
    """Payload para asociar una etiqueta a una sugerencia."""

    suggestion_id: UUID = Field(...)
    tag_id: UUID = Field(...)


class SuggestionTagResponse(BaseModel):
    """Respuesta con datos de la relación sugerencia-etiqueta."""

    suggestion_id: UUID
    tag_id: UUID

    model_config = {"from_attributes": True}
