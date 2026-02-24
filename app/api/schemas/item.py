"""Esquemas Pydantic para la API de Items."""

from uuid import UUID

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Payload para crear un Item."""

    name: str = Field(..., min_length=1)
    description: str | None = None


class ItemResponse(BaseModel):
    """Respuesta con datos de un Item."""

    id: UUID
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
