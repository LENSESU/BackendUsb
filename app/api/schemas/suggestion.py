"""Esquemas Pydantic para sugerencias (contrato HTTP en español)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SuggestionCreate(BaseModel):
    """Payload para crear una sugerencia."""

    model_config = ConfigDict(populate_by_name=True)

    estudiante_id: UUID = Field(
        ...,
        description="ID del estudiante (usuario)",
        alias="student_id",
    )
    titulo: str = Field(
        ...,
        min_length=1,
        max_length=200,
        alias="title",
    )
    contenido: str = Field(
        ...,
        min_length=1,
        alias="content",
    )
    total_votos: int | None = Field(
        default=None,
        ge=0,
        description="Si se omite, se inicializa en 0",
        alias="total_votes",
    )
    foto_id: UUID | None = Field(default=None, alias="photo_id")


class SuggestionUpdate(BaseModel):
    """Payload para actualizar una sugerencia (parcial)."""

    model_config = ConfigDict(populate_by_name=True)

    titulo: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        alias="title",
    )
    contenido: str | None = Field(default=None, min_length=1, alias="content")
    total_votos: int | None = Field(default=None, ge=0, alias="total_votes")
    foto_id: UUID | None = Field(default=None, alias="photo_id")
    comentario_institucional: str | None = Field(
        default=None,
        alias="institutional_comment",
    )


class SuggestionResponse(BaseModel):
    """Respuesta con datos de una sugerencia."""

    id: UUID
    estudiante_id: UUID
    titulo: str
    contenido: str
    total_votos: int
    foto_id: UUID | None
    comentario_institucional: str | None
    created_at: datetime


class SuggestionPopularResponse(BaseModel):
    """Respuesta compacta para ranking de sugerencias populares."""

    id: UUID
    titulo: str
    total_votos: int
