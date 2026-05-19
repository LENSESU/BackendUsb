"""Esquemas Pydantic para sugerencias (contrato HTTP en español)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SuggestionCreate(BaseModel):
    """Payload para crear una sugerencia con etiquetas opcionales."""

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
    etiquetas: list[str] | None = Field(
        default=None,
        description="Lista de nombres de etiquetas (se crean si no existen)",
        alias="tags",
    )
    total_votos: int | None = Field(
        default=None,
        ge=0,
        description="Si se omite, se inicializa en 0",
        alias="total_votes",
    )


class SuggestionUpdate(BaseModel):
    """Payload para actualizar una sugerencia (parcial).

    Solo permite actualizar campos de texto. Para actualizar la foto,
    usa el endpoint específico: PATCH /api/v1/suggestions/{suggestion_id}/photo
    """

    model_config = ConfigDict(populate_by_name=True)

    titulo: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        alias="title",
    )
    contenido: str | None = Field(default=None, min_length=1, alias="content")
    total_votos: int | None = Field(default=None, ge=0, alias="total_votes")
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
    foto_url: str | None
    comentario_institucional: str | None
    created_at: datetime
    etiquetas: list[str] = Field(
        default_factory=list, description="Nombres de las etiquetas asociadas"
    )


class SuggestionPopularResponse(BaseModel):
    """Respuesta para ranking de sugerencias populares."""

    id: UUID
    titulo: str
    total_votos: int
    etiquetas: list[str] = Field(default_factory=list)
    created_at: datetime


class PaginatedSuggestionsResponse(BaseModel):
    """Respuesta paginada para listado de sugerencias."""

    page: int
    limit: int
    total: int
    total_pages: int
    items: list[SuggestionResponse]


class PaginatedPopularSuggestionsResponse(BaseModel):
    """Respuesta paginada para listado de sugerencias populares."""

    page: int
    limit: int
    total: int
    total_pages: int
    items: list[SuggestionPopularResponse]


class InstitutionalCommentRequest(BaseModel):
    """Payload para agregar comentario institucional a una sugerencia."""

    model_config = ConfigDict(populate_by_name=True)

    comentario: str = Field(
        ...,
        min_length=1,
        description="Texto del comentario institucional oficial",
        alias="comment",
    )
