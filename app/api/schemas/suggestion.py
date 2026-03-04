"""Esquemas Pydantic para sugerencias."""

from datetime import datetime

from pydantic import BaseModel, Field


class SuggestionCreate(BaseModel):
    """Payload para crear una sugerencia."""

    student_id: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    photo_id: int | None = Field(default=None, ge=1)


class SuggestionUpdate(BaseModel):
    """Payload para actualizar una sugerencia."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    institutional_comment: str | None = None


class SuggestionResponse(BaseModel):
    """Respuesta con datos de una sugerencia."""

    id: int
    student_id: int
    title: str
    content: str
    photo_id: int | None
    total_votes: int
    institutional_comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

