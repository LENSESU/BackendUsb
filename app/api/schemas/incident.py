"""Esquemas Pydantic para incidentes (contrato HTTP en español)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.incident import IncidentStatus


class Campus(StrEnum):
    """Campus disponibles (enum para Swagger)."""

    FARRALLONES = "Farrallones"
    PARQUE_TECNOLOGICO = "ParqueTecnologico"
    CEDRO = "Cedro"
    LAGO = "Lago"
    NARANJOS = "Naranjos"
    BIBLIOTECA = "Biblioteca"
    CAFETERIA = "Cafeteria"
    PARQUEADERO = "Parqueadero"
    OTRO = "Otro"


class IncidentCreate(BaseModel):
    """Payload para crear un incidente. El estudiante se toma del JWT."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "categoria_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "descripcion": "Descripción detallada del incidente",
                "lugar_campus": ["Biblioteca"],
                "latitud": 3.3759,
                "longitud": -76.5305,
                "prioridad": "Alta",
                "estado": "Nuevo",
                "foto_antes_id": None,
            }
        }
    )

    categoria_id: UUID = Field(..., description="ID de la categoría del incidente")
    descripcion: str = Field(
        ..., min_length=1, description="Descripción detallada del incidente"
    )
    lugar_campus: list[Campus] | None = Field(
        default=None,
        description="Campus seleccionado (array de enums).",
    )
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    estado: IncidentStatus | None = Field(default=None)
    prioridad: str | None = Field(default=None, max_length=20)
    foto_antes_id: UUID | None = Field(default=None)


class IncidentUpdate(BaseModel):
    """Payload para actualizar un incidente."""

    tecnico_id: UUID | None = None
    categoria_id: UUID | None = None
    descripcion: str | None = Field(default=None, min_length=1)
    lugar_campus: list[Campus] | None = Field(default=None)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    estado: IncidentStatus | None = Field(default=None)
    prioridad: str | None = Field(default=None, max_length=20)
    foto_antes_id: UUID | None = None
    foto_despues_id: UUID | None = None


class IncidentResponse(BaseModel):
    """Respuesta con datos de un incidente."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"campus_disponibles": [c.value for c in Campus]},
    )

    id: UUID
    estudiante_id: UUID
    tecnico_id: UUID | None
    categoria_id: UUID
    descripcion: str
    lugar_campus: list[Campus] | None
    latitud: float | None
    longitud: float | None
    estado: IncidentStatus
    prioridad: str | None
    foto_antes_id: UUID | None
    foto_despues_id: UUID | None
    creado_en: datetime
    actualizado_en: datetime | None


def campus_options() -> list[Campus]:
    """Lista fija de campus disponibles para clientes."""

    return list(Campus)
