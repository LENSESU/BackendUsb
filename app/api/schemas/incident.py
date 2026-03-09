"""Esquemas Pydantic para incidentes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    """Payload para crear un incidente. estudiante_id se toma del JWT."""

    category_id: UUID = Field(...)
    description: str = Field(..., min_length=1)
    campus_place: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    priority: str | None = Field(default=None, max_length=20)
    before_photo_id: UUID = Field(...)


class IncidentUpdate(BaseModel):
    """Payload para actualizar un incidente."""

    technician_id: UUID | None = None
    category_id: UUID | None = None
    description: str | None = Field(default=None, min_length=1)
    campus_place: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = Field(default=None, max_length=20)
    priority: str | None = Field(default=None, max_length=20)
    after_photo_id: UUID | None = None


class IncidentResponse(BaseModel):
    """Respuesta con datos de un incidente."""

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
    before_photo_id: UUID
    after_photo_id: UUID | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
