"""Schemas para respuesta consolidada del dashboard."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardUser(BaseModel):
    user_id: UUID
    email: str
    role_id: UUID


class DashboardIncident(BaseModel):
    id: UUID
    category_id: UUID
    categoria: str | None = None
    description: str
    status: str
    priority: str | None
    created_at: datetime


class DashboardSuggestion(BaseModel):
    id: UUID
    titulo: str
    total_votos: int


class DashboardResponse(BaseModel):
    user: DashboardUser
    recentIncidents: list[DashboardIncident]
    suggestions: list[DashboardSuggestion]
