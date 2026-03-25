"""Inyección del servicio de sugerencias."""

from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.application.services.suggestion_service import SuggestionService
from app.infrastructure.adapters.sql_suggestion_repository import (
    SqlSuggestionRepository,
)

_repository: SuggestionRepositoryPort | None = None


def get_suggestion_service() -> SuggestionService:
    global _repository
    if _repository is None:
        _repository = SqlSuggestionRepository()
    return SuggestionService(repository=_repository)
