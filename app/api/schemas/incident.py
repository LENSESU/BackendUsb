"""Esquemas Pydantic para incidentes (contrato HTTP en español)."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.incident import IncidentPriority, IncidentStatus


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
        populate_by_name=True,
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
        },
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
    estado: IncidentStatus | None = Field(default=None, alias="status")
    prioridad: IncidentPriority | None = Field(default=None, alias="priority")
    foto_antes_id: UUID | None = Field(default=None, alias="before_photo_id")


class AssignTechnicianRequest(BaseModel):
    """Payload para asociar un técnico a un incidente (endpoint dedicado)."""

    model_config = ConfigDict(populate_by_name=True)

    tecnico_id: UUID = Field(
        ...,
        description="ID del usuario técnico a asignar",
        alias="technician_id",
    )


class IncidentUpdate(BaseModel):
    """Payload para actualizar campos de un incidente (excluye estado)."""

    model_config = ConfigDict(populate_by_name=True)

    tecnico_id: UUID | None = Field(default=None, alias="technician_id")
    categoria_id: UUID | None = Field(default=None, alias="category_id")
    descripcion: str | None = Field(default=None, min_length=1, alias="description")
    lugar_campus: Campus | None = Field(default=None, alias="campus_place")
    latitud: float | None = Field(default=None, ge=-90, le=90, alias="latitude")
    longitud: float | None = Field(default=None, ge=-180, le=180, alias="longitude")
    prioridad: IncidentPriority | None = Field(default=None, alias="priority")
    foto_antes_id: UUID | None = Field(default=None, alias="before_photo_id")
    foto_despues_id: UUID | None = Field(default=None, alias="after_photo_id")


class IncidentStatusUpdate(BaseModel):
    """Payload para la transición de estado de un incidente."""

    model_config = ConfigDict(populate_by_name=True)

    estado: IncidentStatus = Field(..., alias="status")


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
    before_photo_url: str | None = None
    after_photo_url: str | None = None
    created_at: datetime
    updated_at: datetime | None


class IncidentDetailResponse(IncidentResponse):
    """Respuesta detallada de un incidente con información de estudiante y técnico."""

    student_first_name: str | None = None
    student_last_name: str | None = None
    student_email: str | None = None
    technician_first_name: str | None = None
    technician_last_name: str | None = None
    technician_email: str | None = None


class PaginatedIncidentsResponse(BaseModel):
    """Respuesta paginada para listado de incidentes."""

    page: int
    limit: int
    total: int
    total_pages: int
    items: list[IncidentResponse]


class IncidentEvidenceUploadResponse(BaseModel):
    """Respuesta para carga de evidencia fotográfica de incidente."""

    incident_id: UUID
    filename: str
    content_type: str
    storage_object_name: str | None = None
    file_url: str | None = None
    message: str


class AdminIncidentSummary(BaseModel):
    """Resumen de un incidente para la bandeja del administrador.

    Expone solo los campos necesarios para la vista de lista:
    identificador, categoría, id del técnico, estado, prioridad, fecha, ubicación y
    usuario reportante.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    technician_id: UUID | None
    status: str
    priority: str | None
    created_at: datetime
    location: str | None
    reported_by: UUID
    reporter_email: str | None


class PaginatedAdminIncidentsResponse(BaseModel):
    """Respuesta paginada para la bandeja del administrador."""

    page: int
    limit: int
    total: int
    total_pages: int
    items: list[AdminIncidentSummary]


class IncidentGeoMarker(BaseModel):
    """Marcador geográfico optimizado para visualización en mapa interactivo.

    Contiene solo los campos necesarios para cargar eficientemente marcadores
    de incidentes en un mapa.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "category_name": "Infraestructura",
                "status": "Nuevo",
                "priority": "Alta",
                "latitude": 3.3958,
                "longitude": -76.5317,
                "campus_place": "Central",
                "created_at": "2026-04-16T10:30:00Z",
            }
        },
    )

    id: UUID = Field(..., description="ID único del incidente")
    category_name: str = Field(..., description="Nombre de la categoría del incidente")
    status: str = Field(..., description="Estado actual del incidente")
    priority: str | None = Field(None, description="Nivel de prioridad del incidente")
    latitude: float = Field(..., description="Coordenada de latitud", ge=-90, le=90)
    longitude: float = Field(..., description="Coordenada de longitud", ge=-180, le=180)
    campus_place: str | None = Field(
        None, description="Lugar específico dentro del campus"
    )
    created_at: datetime = Field(..., description="Fecha de creación del incidente")


class PaginatedIncidentsGeoResponse(BaseModel):
    """Respuesta paginada para consulta geográfica de incidentes.

    Optimizada para carga eficiente de marcadores en mapas interactivos.
    """

    page: int = Field(..., ge=1, description="Número de página actual")
    limit: int = Field(
        ..., ge=1, le=100, description="Cantidad de elementos por página"
    )
    total: int = Field(..., ge=0, description="Total de incidentes con coordenadas")
    total_pages: int = Field(..., ge=0, description="Total de páginas")
    items: list[IncidentGeoMarker] = Field(
        ..., description="Lista de marcadores geográficos de incidentes"
    )


class CriticalZoneResponse(BaseModel):
    """Respuesta de una zona crítica del campus."""

    zone: str = Field(..., description="Nombre o identificador de la zona")
    latitude: float | None = Field(None, description="Latitud del centro de la zona")
    longitude: float | None = Field(None, description="Longitud del centro de la zona")
    incident_count: int = Field(..., description="Total de incidentes en la zona")
    score: int = Field(..., description="Puntaje ponderado por prioridad")
    criticality: str = Field(..., description="Nivel de criticidad: Alta, Media o Baja")
