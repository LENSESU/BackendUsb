"""Inyección del servicio de incidentes (repositorios SQL)."""

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_service import IncidentService
from app.infrastructure.adapters.incident_category_repository import (
    SqlAlchemyIncidentCategoryRepository,
)
from app.infrastructure.adapters.postgres_user_repository import (
    PostgresUserRepository,
)
from app.infrastructure.adapters.sql_incident_repository import SqlIncidentRepository

_repository: IncidentRepositoryPort | None = None


def reset_incident_dependencies() -> None:
    """Reinicia cachés de módulo (útil en tests)."""
    global _repository
    _repository = None


def get_incident_service() -> IncidentService:
    """Construye IncidentService con adaptadores SQL compartidos en módulo."""
    global _repository
    if _repository is None:
        _repository = SqlIncidentRepository()
    return IncidentService(
        repository=_repository,
        category_repository=SqlAlchemyIncidentCategoryRepository(),
        user_repository=PostgresUserRepository(),
    )
