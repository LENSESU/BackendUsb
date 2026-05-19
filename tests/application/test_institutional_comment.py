"""Tests para la lógica de comentario institucional """

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.application.services.suggestion_service import SuggestionService
from app.domain.entities.suggestion import Suggestion


class InMemorySuggestionRepository:
    def __init__(self) -> None:
        self._store: dict = {}

    def get_by_id(self, suggestion_id):
        return self._store.get(suggestion_id)

    def list_all(self):
        return list(self._store.values())

    def list_by_student(self, student_id):
        return [s for s in self._store.values() if s.student_id == student_id]

    def list_popular(self, limit=5):
        return sorted(self._store.values(), key=lambda s: s.total_votes, reverse=True)[:limit]

    def list_filtered(self, order_by="fecha", tags=None):
        return list(self._store.values())

    def save(self, suggestion):
        self._store[suggestion.id] = suggestion
        return suggestion

    def save_with_tags(self, suggestion, tag_names=None):
        return self.save(suggestion)

    def delete(self, suggestion_id):
        return self._store.pop(suggestion_id, None) is not None


def _make_suggestion() -> Suggestion:
    return Suggestion(
        id=uuid4(),
        student_id=uuid4(),
        title="Sugerencia de prueba",
        content="Contenido de prueba",
    )


def test_agrega_comentario_institucional() -> None:
    repo = InMemorySuggestionRepository()
    suggestion = _make_suggestion()
    repo.save(suggestion)
    service = SuggestionService(repository=repo)

    result = service.add_institutional_comment(suggestion.id, "Respuesta oficial")

    assert result is not None
    assert result.institutional_comment == "Respuesta oficial"


def test_reemplaza_comentario_existente() -> None:
    repo = InMemorySuggestionRepository()
    suggestion = _make_suggestion()
    repo.save(suggestion)
    service = SuggestionService(repository=repo)

    service.add_institutional_comment(suggestion.id, "Primer comentario")
    result = service.add_institutional_comment(suggestion.id, "Comentario actualizado")

    assert result.institutional_comment == "Comentario actualizado"


def test_retorna_none_si_no_existe() -> None:
    repo = InMemorySuggestionRepository()
    service = SuggestionService(repository=repo)

    result = service.add_institutional_comment(uuid4(), "Comentario")

    assert result is None


def test_limpia_espacios_del_comentario() -> None:
    repo = InMemorySuggestionRepository()
    suggestion = _make_suggestion()
    repo.save(suggestion)
    service = SuggestionService(repository=repo)

    result = service.add_institutional_comment(suggestion.id, "  Respuesta  ")

    assert result.institutional_comment == "Respuesta"