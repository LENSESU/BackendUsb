"""Caso de uso: registro de votos en sugerencias."""

from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.application.ports.vote_repository import VoteRepositoryPort
from app.domain.entities.suggestion import Suggestion
from app.domain.entities.vote import Vote


class VoteService:
    """Orquesta el registro de votos garantizando unicidad por estudiante."""

    def __init__(
        self,
        vote_repository: VoteRepositoryPort,
        suggestion_repository: SuggestionRepositoryPort,
    ) -> None:
        self._votes = vote_repository
        self._suggestions = suggestion_repository

    def cast_vote(self, student_id: UUID, suggestion_id: UUID) -> Vote:
        """Registra el voto del estudiante e incrementa el contador de la sugerencia.

        Raises:
            HTTPException 404 si la sugerencia no existe.
            HTTPException 409 si el estudiante ya votó esta sugerencia.
        """
        suggestion = self._suggestions.get_by_id(suggestion_id)
        if suggestion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Sugerencia no encontrada",
                    "error_code": "SUGGESTION_NOT_FOUND",
                },
            )

        existing = self._votes.get_by_student_and_suggestion(student_id, suggestion_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "El estudiante ya registró un voto para esta sugerencia",
                    "error_code": "VOTE_ALREADY_EXISTS",
                },
            )

        vote = Vote(id=uuid4(), student_id=student_id, suggestion_id=suggestion_id)
        saved_vote = self._votes.save(vote)

        updated_suggestion = Suggestion(
            id=suggestion.id,
            student_id=suggestion.student_id,
            title=suggestion.title,
            content=suggestion.content,
            photo_id=suggestion.photo_id,
            total_votes=suggestion.total_votes + 1,
            institutional_comment=suggestion.institutional_comment,
            created_at=suggestion.created_at,
        )
        self._suggestions.save(updated_suggestion)

        return saved_vote
