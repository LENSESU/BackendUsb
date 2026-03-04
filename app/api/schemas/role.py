"""Esquemas Pydantic para la API de Roles."""

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """Payload para crear un rol."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=200)


class RoleResponse(BaseModel):
    """Respuesta con datos de un rol."""

    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}
