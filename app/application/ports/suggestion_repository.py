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
    def list_by_student(self, student_id: UUID) -> list[Suggestion]:
        """Lista las sugerencias creadas por un estudiante."""
        ...

    @abstractmethod
    def list_popular(self, limit: int) -> list[Suggestion]:
        """Lista sugerencias populares por votos descendente."""
        ...

    @abstractmethod
    def list_filtered(
        self,
        order_by: str = "fecha",
        tags: list[str] | None = None,
    ) -> list[Suggestion]:
        """Lista sugerencias con ordenamiento y filtro por etiquetas opcional.

        Args:
            order_by: ``"fecha"`` (más reciente primero) o ``"popularidad"``
                      (más votos primero).
            tags: si se indica, sólo se devuelven sugerencias que posean al
                  menos una de las etiquetas de la lista.
        """
        ...

    @abstractmethod
    def save(self, suggestion: Suggestion) -> Suggestion:
        """Guarda o actualiza una sugerencia."""
        ...

    @abstractmethod
    def save_with_tags(
        self, suggestion: Suggestion, tag_names: list[str] | None = None
    ) -> Suggestion:
        """Guarda una sugerencia y asocia etiquetas (crea si no existen)."""
        ...

    @abstractmethod
    def delete(self, suggestion_id: UUID) -> bool:
        """Elimina una sugerencia por ID. Retorna True si existía."""
        ...

    @abstractmethod
    def increment_votes(self, suggestion_id: UUID) -> None:
        """Incrementa atómicamente el contador de votos de una sugerencia."""
        ...
