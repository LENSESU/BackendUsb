"""Esquemas Pydantic para votos."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    """Payload para registrar un voto."""

    student_id: UUID = Field(...)
    suggestion_id: UUID = Field(...)


class VoteResponse(BaseModel):
    """Respuesta con datos de un voto."""

    id: UUID
    student_id: UUID
    suggestion_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
