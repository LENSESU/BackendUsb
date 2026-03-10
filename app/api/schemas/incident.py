"""Esquemas Pydantic para incidentes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    """Payload para crear un incidente. El estudiante se toma del JWT."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "descripcion": "Descripción detallada del incidente",
                "lugar_campus": "Edificio A, primer piso",
                "latitud": 3.3759,
                "longitud": -76.5305,
                "prioridad": "Alta",
                "estado": "Nuevo",
                "foto_antes_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            }
        },
    )

    categoria_id: UUID = Field(
        ...,
        description="ID de la categoría del incidente",
    )
    descripcion: str = Field(
        ...,
        min_length=1,
        description="Descripción detallada del incidente",
    )
    lugar_campus: str | None = Field(
        default=None,
        max_length=200,
        description="Lugar dentro del campus donde ocurrió",
    )
    latitud: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitud de la ubicación",
    )
    longitud: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitud de la ubicación",
    )
    prioridad: str | None = Field(
        default=None,
        max_length=20,
        description="Prioridad del incidente (ej: Alta, Media, Baja)",
    )
    estado: str | None = Field(
        default=None,
        max_length=20,
        description="Estado inicial (ej: Nuevo, En progreso). Si no se envía, se usa Nuevo.",
    )
    foto_antes_id: UUID | None = Field(
        default=None,
        description="ID del archivo con la foto del estado anterior",
    )


class IncidentUpdate(BaseModel):
    """Payload para actualizar un incidente."""

    tecnico_id: UUID | None = Field(
        default=None,
        description="ID del técnico asignado",
    )
    categoria_id: UUID | None = Field(
        default=None,
        description="ID de la categoría",
    )
    descripcion: str | None = Field(
        default=None,
        min_length=1,
        description="Descripción actualizada",
    )
    lugar_campus: str | None = Field(
        default=None,
        max_length=200,
        description="Lugar dentro del campus",
    )
    latitud: float | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="Latitud",
    )
    longitud: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="Longitud",
    )
    estado: str | None = Field(
        default=None,
        max_length=20,
        description="Estado actual (ej: Nuevo, En progreso, Resuelto)",
    )
    prioridad: str | None = Field(
        default=None,
        max_length=20,
        description="Prioridad",
    )
    foto_antes_id: UUID | None = Field(
        default=None,
        description="ID de la foto antes",
    )
    foto_despues_id: UUID | None = Field(
        default=None,
        description="ID de la foto después de la resolución",
    )


class IncidentResponse(BaseModel):
    """Respuesta con datos de un incidente."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "estudiante_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "tecnico_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "categoria_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "descripcion": "Descripción del incidente reportado",
                "lugar_campus": "Edificio A, primer piso",
                "latitud": 3.3759,
                "longitud": -76.5305,
                "estado": "Nuevo",
                "prioridad": "Alta",
                "foto_antes_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "foto_despues_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "creado_en": "2026-03-09T23:00:26.478Z",
                "actualizado_en": "2026-03-09T23:00:26.478Z",
            }
        },
    )

    id: UUID = Field(description="ID único del incidente")
    estudiante_id: UUID = Field(
        description="ID del estudiante que reportó",
    )
    tecnico_id: UUID | None = Field(
        default=None,
        description="ID del técnico asignado",
    )
    categoria_id: UUID = Field(description="ID de la categoría")
    descripcion: str = Field(description="Descripción del incidente")
    lugar_campus: str | None = Field(
        default=None,
        description="Lugar en el campus",
    )
    latitud: float | None = Field(
        default=None,
        description="Latitud de la ubicación",
    )
    longitud: float | None = Field(
        default=None,
        description="Longitud de la ubicación",
    )
    estado: str = Field(
        description="Estado actual (Nuevo, En progreso, Resuelto)",
    )
    prioridad: str | None = Field(
        default=None,
        description="Prioridad del incidente",
    )
    foto_antes_id: UUID | None = Field(
        default=None,
        description="ID de la foto del estado anterior",
    )
    foto_despues_id: UUID | None = Field(
        default=None,
        description="ID de la foto después de la resolución",
    )
    creado_en: datetime = Field(
        description="Fecha y hora de creación",
    )
    actualizado_en: datetime | None = Field(
        default=None,
        description="Fecha y hora de última actualización",
    )
