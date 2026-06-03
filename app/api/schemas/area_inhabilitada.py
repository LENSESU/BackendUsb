# app/api/schemas/area_inhabilitada.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.api.schemas.incident import Campus  # ← importar el enum existente


class AreaInhabilitadaCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    motivo: str = Field(..., min_length=1)
    fecha_inicio: datetime
    descripcion: str | None = Field(default=None, max_length=300)
    fecha_fin: datetime | None = None
    lugar_campus: Campus | None = Field(  # ← era str, ahora enum validado
        default=None, max_length=200
    )
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    incidente_id: UUID | None = Field(  # ← NUEVO: incidente a asociar al crear
        default=None,
        description=(
            "ID del incidente a asociar al registrar el área. "
            "Requerido si el solicitante es Técnico."
        ),
    )


class AreaInhabilitadaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    motivo: str | None = Field(default=None, min_length=1)
    descripcion: str | None = Field(default=None, max_length=300)
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    activa: bool | None = None
    lugar_campus: Campus | None = None  # ← era str, ahora enum
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)


class AreaInhabilitadaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nombre: str
    motivo: str
    descripcion: str | None
    fecha_inicio: datetime
    fecha_fin: datetime | None
    activa: bool
    lugar_campus: str | None
    latitud: float | None
    longitud: float | None
    registrada_por_id: UUID | None  # ya existe en el modelo ORM
    created_at: datetime | None
    updated_at: datetime | None


class AreaInhabilitadaListResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    items: list[AreaInhabilitadaResponse]


class AsociarIncidenteRequest(BaseModel):
    incidente_id: UUID = Field(..., description="ID del incidente a asociar")


class IncidenteAsociadoResponse(BaseModel):
    id: UUID
    descripcion: str
    status: str
    priority: str | None
    campus_place: str | None
    created_at: datetime


class AreaAsociadaResponse(BaseModel):
    id: UUID
    nombre: str
    motivo: str
    activa: bool
    lugar_campus: str | None
    fecha_inicio: datetime
    fecha_fin: datetime | None
