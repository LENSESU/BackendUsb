"""Inyección del servicio de incidentes (repositorios SQL)."""

from app.application.ports.incident_category_repository import (
    IncidentCategoryRepositoryPort,
)
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_service import IncidentService
from app.infrastructure.adapters.incident_category_repository import (
    SqlAlchemyIncidentCategoryRepository,
)
from app.infrastructure.adapters.sql_incident_repository import SqlIncidentRepository

_repository: IncidentRepositoryPort | None = None
_UNSET = object()
_category_repository: IncidentCategoryRepositoryPort | None = _UNSET  # type: ignore[assignment]


def reset_incident_dependencies() -> None:
    """Reinicia cachés de módulo (útil en tests)."""
    global _repository, _category_repository
    _repository = None
    _category_repository = _UNSET  # type: ignore[assignment]


def get_incident_service() -> IncidentService:
    """Construye IncidentService con adaptadores SQL compartidos en módulo."""
    global _repository
    if _repository is None:
        _repository = SqlIncidentRepository()
    cat_repo = (
        SqlAlchemyIncidentCategoryRepository()
        if _category_repository is _UNSET
        else _category_repository
    )
    return IncidentService(
        repository=_repository,
        category_repository=cat_repo,
    )
