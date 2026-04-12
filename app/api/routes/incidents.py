"""Rutas HTTP para Incidents. Traduce request/response y delega en el caso de uso."""

from fastapi import APIRouter

from app.api.schemas.incident import IncidentSummary
from app.application.ports import IncidentRepositoryPort
from app.application.services import IncidentService

router = APIRouter()

_repository: IncidentRepositoryPort | None = None


def get_incident_service() -> IncidentService:
    """Obtiene el servicio de Incidents.

    En producción vendría de un contenedor de DI.
    """
    global _repository
    from app.infrastructure.adapters import InMemoryIncidentRepository

    if _repository is None:
        _repository = InMemoryIncidentRepository()
    return IncidentService(repository=_repository)


@router.get("/", response_model=list[IncidentSummary])
def list_incidents() -> list[IncidentSummary]:
    """Lista todos los incidentes ordenados del más reciente al más antiguo."""
    service = get_incident_service()
    incidents = service.list_incidents()
    return [IncidentSummary.model_validate(i) for i in incidents]
