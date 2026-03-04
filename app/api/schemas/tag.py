"""Esquemas Pydantic para etiquetas."""

from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    """Payload para crear una etiqueta."""

    name: str = Field(..., min_length=1, max_length=80)


class TagResponse(BaseModel):
    """Respuesta con datos de una etiqueta."""

    id: int
    name: str

    model_config = {"from_attributes": True}
