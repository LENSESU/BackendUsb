"""Esquemas HTTP para consulta de técnicos (sin datos sensibles)."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AvailableTechnicianResponse(BaseModel):
    """Datos públicos de un técnico disponible para asignación."""

    id: UUID = Field(..., description="Identificador del usuario técnico")
    first_name: str = Field(..., description="Nombre")
    last_name: str = Field(..., description="Apellido")
    email: EmailStr = Field(..., description="Correo institucional")

    model_config = {"from_attributes": True}
