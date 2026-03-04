"""Esquemas Pydantic para votos."""

from datetime import datetime

from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    """Payload para registrar un voto."""

    student_id: int = Field(..., ge=1)
    suggestion_id: int = Field(..., ge=1)


class VoteResponse(BaseModel):
    """Respuesta con datos de un voto."""

    id: int
    student_id: int
    suggestion_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
