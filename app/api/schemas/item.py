"""Esquemas Pydantic para la API de Items.

Modificación para #63 (Validar accesos cruzados):
  Se añadió ``owner_id`` en ``ItemResponse`` para que el frontend pueda
  conocer el dueño de cada item y adaptar la UI (ej. mostrar/ocultar
  botón de eliminar).  El ``owner_id`` NO se recibe en ``ItemCreate``;
  se asigna automáticamente desde el JWT del usuario autenticado.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Payload para crear un Item.  El owner_id NO se envía aquí; se asigna del JWT."""

    name: str = Field(..., min_length=1)
    description: str | None = None


class ItemResponse(BaseModel):
    """Respuesta con datos de un Item."""

    id: UUID
    name: str
    description: str | None = None
    # [NUEVO – #63] UUID del usuario dueño del item.  None para items legacy.
    owner_id: UUID | None = None

    model_config = {"from_attributes": True}
