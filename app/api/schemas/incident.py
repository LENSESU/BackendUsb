"""Esquemas Pydantic para la API de Incidents."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.entities.incident import IncidentCategory, IncidentPriority, IncidentStatus


class IncidentSummary(BaseModel):
    """Respuesta resumida de un incidente para la bandeja del administrador."""

    id: UUID
    title: str
    category: IncidentCategory
    status: IncidentStatus
    priority: IncidentPriority
    location: str | None
    reported_by: str
    created_at: datetime

    model_config = {"from_attributes": True}
