"""Inyección del servicio de técnicos (repositorios SQL)."""

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.ports.technician_repository import TechnicianRepositoryPort
from app.application.services.technician_service import TechnicianService
from app.infrastructure.adapters.sql_incident_repository import SqlIncidentRepository
from app.infrastructure.adapters.sql_technician_repository import (
    SqlTechnicianRepository,
)

_technician_repository: TechnicianRepositoryPort | None = None
_incident_repository_for_technician: IncidentRepositoryPort | None = None


def reset_technician_dependencies() -> None:
    """Reinicia cachés de módulo (útil en tests)."""
    global _technician_repository, _incident_repository_for_technician
    _technician_repository = None
    _incident_repository_for_technician = None


def get_technician_service() -> TechnicianService:
    """Construye TechnicianService con adaptadores SQL compartidos en módulo."""
    global _technician_repository, _incident_repository_for_technician
    if _incident_repository_for_technician is None:
        _incident_repository_for_technician = SqlIncidentRepository()
    if _technician_repository is None:
        _technician_repository = SqlTechnicianRepository()
    return TechnicianService(
        technician_repository=_technician_repository,
        incident_repository=_incident_repository_for_technician,
    )
