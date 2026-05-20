"""Caso de uso: registro de votos en sugerencias."""

from uuid import UUID, uuid4

from fastapi import HTTPException, status

from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.application.ports.vote_repository import VoteRepositoryPort
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

        self._suggestions.increment_votes(suggestion_id)

        return saved_vote
