"""Esquemas Pydantic para incidentes (contrato HTTP en español)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Campus(StrEnum):
    """Campus disponibles (enum para Swagger)."""

    BIBLIOTECA = "Biblioteca"
    LAGO = "Lago"
    CEDRO = "Cedro"
    CENTRAL = "Central"
    FARRALLONES = "Farrallones"
    PARQUEADERO_ESTUDIANTES = "Parqueadero_estudiantes"
    PARQUE_TECNOLOGICO = "Parque tecnologico"
    NARANJOS = "Naranjos"
    HIGUERONES = "Higuerones"
    CANCHA = "Cancha"
    OTROS = "Otros"


class IncidentCreate(BaseModel):
    """Payload para crear un incidente. El estudiante se toma del JWT."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "descripcion": "Descripción detallada del incidente",
                "lugar_campus": "Biblioteca",
                "latitud": 3.3759,
                "longitud": -76.5305,
                "prioridad": "Alta",
                "estado": "Nuevo",
                "foto_antes_id": None,
            }
        }
    )

    categoria_id: UUID = Field(
        ...,
        description="ID de la categoría del incidente",
        alias="category_id",
    )
    descripcion: str = Field(
        ...,
        min_length=1,
        description="Descripción detallada del incidente",
        alias="description",
    )
    # Para compatibilidad con los tests API, aceptamos ``campus_place`` (str)
    # como alias de ``lugar_campus``.
    lugar_campus: Campus | None = Field(
        default=None,
        description="Lugar específico dentro del campus.",
        alias="campus_place",
    )
    latitud: float | None = Field(default=None, ge=-90, le=90, alias="latitude")
    longitud: float | None = Field(default=None, ge=-180, le=180, alias="longitude")
    estado: str | None = Field(default=None, max_length=20, alias="status")
    prioridad: str | None = Field(default=None, max_length=20, alias="priority")
    foto_antes_id: UUID | None = Field(default=None, alias="before_photo_id")


class IncidentUpdate(BaseModel):
    """Payload para actualizar un incidente."""

    tecnico_id: UUID | None = Field(default=None, alias="technician_id")
    categoria_id: UUID | None = Field(default=None, alias="category_id")
    descripcion: str | None = Field(default=None, min_length=1, alias="description")
    lugar_campus: Campus | None = Field(default=None, alias="campus_place")
    latitud: float | None = Field(default=None, ge=-90, le=90, alias="latitude")
    longitud: float | None = Field(default=None, ge=-180, le=180, alias="longitude")
    estado: str | None = Field(default=None, max_length=20, alias="status")
    prioridad: str | None = Field(default=None, max_length=20, alias="priority")
    foto_antes_id: UUID | None = Field(default=None, alias="before_photo_id")
    foto_despues_id: UUID | None = Field(default=None, alias="after_photo_id")


class IncidentResponse(BaseModel):
    """Respuesta con datos de un incidente."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"campus_disponibles": [c.value for c in Campus]},
    )

    id: UUID
    student_id: UUID
    technician_id: UUID | None
    category_id: UUID
    description: str
    campus_place: str | None
    latitude: float | None
    longitude: float | None
    status: str
    priority: str | None
    before_photo_id: UUID | None
    after_photo_id: UUID | None
    created_at: datetime
    updated_at: datetime | None


class IncidentEvidenceUploadResponse(BaseModel):
    """Respuesta para carga de evidencia fotográfica de incidente."""

    incident_id: UUID
    filename: str
    content_type: str
    storage_object_name: str | None = None
    file_url: str | None = None
    message: str
