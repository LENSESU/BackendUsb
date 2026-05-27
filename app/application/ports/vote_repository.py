"""Puerto (interfaz) para persistencia de Votos."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.vote import Vote


class VoteRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Votos."""

    @abstractmethod
    def get_by_student_and_suggestion(
        self, student_id: UUID, suggestion_id: UUID
    ) -> Vote | None:
        """Retorna el voto del estudiante para una sugerencia, o None si no existe."""
        ...

    @abstractmethod
    def save(self, vote: Vote) -> Vote:
        """Persiste un voto y retorna la entidad guardada."""
        ...
