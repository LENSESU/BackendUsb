"""Esquemas Pydantic para sugerencias."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SuggestionCreate(BaseModel):
    """Payload para crear una sugerencia."""

    student_id: UUID = Field(...)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    photo_id: UUID | None = None


class SuggestionUpdate(BaseModel):
    """Payload para actualizar una sugerencia."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    institutional_comment: str | None = None


class SuggestionResponse(BaseModel):
    """Respuesta con datos de una sugerencia."""

    id: UUID
    student_id: UUID
    title: str
    content: str
    photo_id: UUID | None
    total_votes: int
    institutional_comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
