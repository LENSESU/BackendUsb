"""Puerto (interfaz) para persistencia de sugerencias."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.suggestion import Suggestion


class SuggestionRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de sugerencias."""

    @abstractmethod
    def get_by_id(self, suggestion_id: UUID) -> Suggestion | None:
        """Obtiene una sugerencia por su ID."""
        ...

    @abstractmethod
    def list_all(self) -> list[Suggestion]:
        """Lista todas las sugerencias."""
        ...

    @abstractmethod
    def list_popular(self, limit: int) -> list[Suggestion]:
        """Lista sugerencias populares por votos descendente."""
        ...

    @abstractmethod
    def save(self, suggestion: Suggestion) -> Suggestion:
        """Guarda o actualiza una sugerencia."""
        ...

    @abstractmethod
    def delete(self, suggestion_id: UUID) -> bool:
        """Elimina una sugerencia por ID. Retorna True si existía."""
        ...
