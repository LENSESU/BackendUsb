"""Esquemas Pydantic para incidentes."""

from datetime import datetime

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    """Payload para crear un incidente."""

    student_id: int = Field(..., ge=1)
    category_id: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    campus_place: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    priority: str | None = Field(default=None, max_length=20)
    before_photo_id: int = Field(..., ge=1)


class IncidentUpdate(BaseModel):
    """Payload para actualizar un incidente."""

    technician_id: int | None = Field(default=None, ge=1)
    category_id: int | None = Field(default=None, ge=1)
    description: str | None = Field(default=None, min_length=1)
    campus_place: str | None = Field(default=None, max_length=200)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    status: str | None = Field(default=None, max_length=20)
    priority: str | None = Field(default=None, max_length=20)
    after_photo_id: int | None = Field(default=None, ge=1)


class IncidentResponse(BaseModel):
    """Respuesta con datos de un incidente."""

    id: int
    student_id: int
    technician_id: int | None
    category_id: int
    description: str
    campus_place: str | None
    latitude: float | None
    longitude: float | None
    status: str
    priority: str | None
    before_photo_id: int
    after_photo_id: int | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
