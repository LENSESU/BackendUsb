"""Adaptador in-memory para Votos (desarrollo y tests)."""

from uuid import UUID

from app.application.ports.vote_repository import VoteRepositoryPort
from app.domain.entities.vote import Vote


class InMemoryVoteRepository(VoteRepositoryPort):
    """Almacén en memoria — útil para tests sin base de datos."""

    def __init__(self) -> None:
        self._store: list[Vote] = []

    def get_by_student_and_suggestion(
        self, student_id: UUID, suggestion_id: UUID
    ) -> Vote | None:
        for vote in self._store:
            if vote.student_id == student_id and vote.suggestion_id == suggestion_id:
                return vote
        return None

    def save(self, vote: Vote) -> Vote:
        self._store.append(vote)
        return vote
