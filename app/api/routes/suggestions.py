"""Rutas HTTP para sugerencias."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import require_role
from app.api.dependencies.suggestion import get_suggestion_service
from app.api.schemas.suggestion import (
    SuggestionCreate,
    SuggestionResponse,
    SuggestionUpdate,
)
from app.application.services.suggestion_service import SuggestionService
from app.domain.entities.suggestion import Suggestion

router = APIRouter()


def _to_response(s: Suggestion) -> SuggestionResponse:
    if s.id is None or s.created_at is None:
        msg = "La sugerencia persistida debe tener id y created_at"
        raise RuntimeError(msg)
    return SuggestionResponse(
        id=s.id,
        estudiante_id=s.student_id,
        titulo=s.title,
        contenido=s.content,
        total_votos=s.total_votes,
        foto_id=s.photo_id,
        comentario_institucional=s.institutional_comment,
        created_at=s.created_at,
        puntuacion_sentimiento=s.sentiment_score,
        sentimiento=None,
    )


@router.get(
    "/",
    response_model=list[SuggestionResponse],
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_suggestions(
    service: SuggestionService = Depends(get_suggestion_service),
) -> list[SuggestionResponse]:
    return [_to_response(s) for s in service.list_all()]


@router.get(
    "/{suggestion_id}",
    response_model=SuggestionResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_suggestion(
    suggestion_id: UUID,
    service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestionResponse:
    suggestion = service.get_by_id(suggestion_id)
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sugerencia no encontrada",
        )
    return _to_response(suggestion)


@router.post(
    "/",
    response_model=SuggestionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def create_suggestion(
    payload: SuggestionCreate,
    service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestionResponse:
    try:
        suggestion = service.create(
            student_id=payload.estudiante_id,
            title=payload.titulo,
            content=payload.contenido,
            total_votes=payload.total_votos,
            photo_id=payload.foto_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return _to_response(suggestion)


@router.patch(
    "/{suggestion_id}",
    response_model=SuggestionResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def update_suggestion(
    suggestion_id: UUID,
    payload: SuggestionUpdate,
    service: SuggestionService = Depends(get_suggestion_service),
) -> SuggestionResponse:
    partial = payload.model_dump(exclude_unset=True)
    try:
        suggestion = service.update(suggestion_id, partial)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sugerencia no encontrada",
        )
    return _to_response(suggestion)


@router.delete(
    "/{suggestion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def delete_suggestion(
    suggestion_id: UUID,
    service: SuggestionService = Depends(get_suggestion_service),
) -> None:
    deleted = service.delete(suggestion_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sugerencia no encontrada",
        )
