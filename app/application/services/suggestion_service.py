"""Caso de uso: operaciones sobre sugerencias."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID, uuid4

from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.domain.entities.suggestion import Suggestion


class SuggestionService:
    """Servicio de aplicación para sugerencias."""

    def __init__(self, repository: SuggestionRepositoryPort) -> None:
        self._repository = repository

    def get_by_id(self, suggestion_id: UUID) -> Suggestion | None:
        return self._repository.get_by_id(suggestion_id)

    def list_all(self) -> list[Suggestion]:
        return self._repository.list_all()

    def list_by_student(self, student_id: UUID) -> list[Suggestion]:
        return self._repository.list_by_student(student_id)

    def list_popular(self, limit: int = 5) -> list[Suggestion]:
        return self._repository.list_popular(limit=limit)

    def list_filtered(
        self,
        order_by: str = "fecha",
        tags: list[str] | None = None,
    ) -> list[Suggestion]:
        """Lista sugerencias con ordenamiento y filtro opcional por etiquetas."""
        return self._repository.list_filtered(order_by=order_by, tags=tags)

    def get_top_suggestions(self, limit: int = 5) -> list[Suggestion]:
        """Alias semántico para dashboard: top sugerencias por votos."""
        return self.list_popular(limit=limit)

    def create(
        self,
        student_id: UUID,
        title: str,
        content: str,
        total_votes: int | None = None,
        photo_id: UUID | None = None,
        tags: list[str] | None = None,
    ) -> Suggestion:
        votes = 0 if total_votes is None else total_votes
        suggestion = Suggestion(
            id=uuid4(),
            student_id=student_id,
            title=title.strip(),
            content=content.strip(),
            photo_id=photo_id,
            total_votes=votes,
            tags=tags or [],
        )
        if tags:
            return self._repository.save_with_tags(suggestion, tags)
        return self._repository.save(suggestion)

    def update(
        self, suggestion_id: UUID, partial: Mapping[str, Any]
    ) -> Suggestion | None:
        existing = self._repository.get_by_id(suggestion_id)
        if existing is None:
            return None

        title = partial.get("titulo", existing.title)
        content = partial.get("contenido", existing.content)
        if "total_votos" in partial and partial["total_votos"] is None:
            raise ValueError("El campo total_votos no puede ser nulo")
        total_votes = partial.get("total_votos", existing.total_votes)
        photo_id = partial.get("foto_id", existing.photo_id)
        institutional_comment = partial.get(
            "comentario_institucional", existing.institutional_comment
        )

        updated = Suggestion(
            id=existing.id,
            student_id=existing.student_id,
            title=title,
            content=content,
            photo_id=photo_id,
            total_votes=total_votes,
            institutional_comment=institutional_comment,
            created_at=existing.created_at,
            tags=existing.tags or [],
        )
        return self._repository.save(updated)

    def delete(self, suggestion_id: UUID) -> bool:
        return self._repository.delete(suggestion_id)

    def add_institutional_comment(
        self,
        suggestion_id: UUID,
        comment: str,
    ) -> Suggestion | None:
        """Agrega o reemplaza el comentario institucional de una sugerencia."""
        existing = self._repository.get_by_id(suggestion_id)
        if existing is None:
            return None
        updated = Suggestion(
            id=existing.id,
            student_id=existing.student_id,
            title=existing.title,
            content=existing.content,
            photo_id=existing.photo_id,
            total_votes=existing.total_votes,
            institutional_comment=comment.strip(),
            created_at=existing.created_at,
            tags=existing.tags or [],
        )
        return self._repository.save(updated)
