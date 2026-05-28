"""Esquemas HTTP para gestión y consulta de técnicos."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class AvailableTechnicianResponse(BaseModel):
    """Datos públicos de un técnico disponible para asignación."""

    id: UUID = Field(..., description="Identificador del usuario técnico")
    first_name: str = Field(..., description="Nombre")
    last_name: str = Field(..., description="Apellido")
    email: EmailStr = Field(..., description="Correo institucional")

    model_config = {"from_attributes": True}


class TechnicianCreateRequest(BaseModel):
    """Payload para registrar un nuevo técnico."""

    first_name: str = Field(..., min_length=1, max_length=100, description="Nombre")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellido")
    email: EmailStr = Field(..., description="Correo institucional")
    password: str = Field(..., min_length=8, description="Contraseña inicial")


class TechnicianUpdateRequest(BaseModel):
    """Payload para actualizar datos de un técnico (todos opcionales)."""

    first_name: str | None = Field(
        None, min_length=1, max_length=100, description="Nuevo nombre"
    )
    last_name: str | None = Field(
        None, min_length=1, max_length=100, description="Nuevo apellido"
    )
    email: EmailStr | None = Field(None, description="Nuevo correo institucional")


class TechnicianAdminResponse(BaseModel):
    """Vista completa de un técnico para el panel de administración."""

    id: UUID = Field(..., description="Identificador")
    first_name: str = Field(..., description="Nombre")
    last_name: str = Field(..., description="Apellido")
    email: EmailStr = Field(..., description="Correo")
    is_active: bool = Field(..., description="Si el técnico está activo")
    created_at: datetime = Field(..., description="Fecha de registro")

    model_config = {"from_attributes": True}


class TechnicianIncidentSummary(BaseModel):
    """Resumen de un incidente asignado a un técnico."""

    id: UUID = Field(..., description="ID del incidente")
    description: str = Field(..., description="Descripción del incidente")
    status: str = Field(..., description="Estado actual")
    priority: str | None = Field(None, description="Prioridad")
    campus_place: str | None = Field(None, description="Lugar en campus")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime | None = Field(None, description="Última actualización")

    model_config = {"from_attributes": True}


class TechnicianIncidentsResponse(BaseModel):
    """Técnico con lista de incidentes asignados."""

    technician: TechnicianAdminResponse
    incidents: list[TechnicianIncidentSummary]
    total: int = Field(..., description="Total de incidentes asignados")
