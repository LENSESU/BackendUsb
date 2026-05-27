from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AreaInhabilitadaCreate(BaseModel):
    nombre: str = Field(
        ..., min_length=1, max_length=150, description="Nombre del área"
    )
    motivo: str = Field(..., min_length=1, description="Motivo de inhabilitación")
    fecha_inicio: datetime = Field(
        ..., description="Fecha y hora de inicio de la inhabilitación"
    )
    descripcion: str | None = Field(
        default=None, max_length=300, description="Descripción adicional"
    )
    fecha_fin: datetime | None = Field(
        default=None, description="Fecha estimada de rehabilitación"
    )
    lugar_campus: str | None = Field(default=None, description="Lugar del campus")
    latitud: float | None = Field(default=None, ge=-90, le=90, description="Latitud")
    longitud: float | None = Field(
        default=None, ge=-180, le=180, description="Longitud"
    )


class AreaInhabilitadaUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    motivo: str | None = Field(default=None, min_length=1)
    descripcion: str | None = Field(default=None, max_length=300)
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    activa: bool | None = None
    lugar_campus: str | None = None
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
    registrada_por_id: UUID | None
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
    """Resumen de un incidente asociado a un área inhabilitada."""

    id: UUID
    descripcion: str
    status: str
    priority: str | None
    campus_place: str | None
    created_at: datetime


class AreaAsociadaResponse(BaseModel):
    """Resumen de un área inhabilitada asociada a un incidente."""

    id: UUID
    nombre: str
    motivo: str
    activa: bool
    lugar_campus: str | None
    fecha_inicio: datetime
    fecha_fin: datetime | None
