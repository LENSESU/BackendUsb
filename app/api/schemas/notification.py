"""Esquemas Pydantic para notificaciones."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    """Payload para crear una notificación."""

    user_id: UUID = Field(...)
    incident_id: UUID = Field(...)
    message: str = Field(..., min_length=1, max_length=300)


class NotificationUpdate(BaseModel):
    """Payload para actualizar el estado de una notificación."""

    is_read: bool = Field(...)


class NotificationResponse(BaseModel):
    """Respuesta con datos de una notificación."""

    id: UUID
    user_id: UUID
    incident_id: UUID
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
