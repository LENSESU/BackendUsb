from app.application.services.incidente_area_service import IncidenteAreaService
from app.infrastructure.adapters.area_inhabilitada_repository import (
    SqlAlchemyAreaInhabilitadaRepository,
)
from app.infrastructure.adapters.incidente_area_repository import (
    SqlAlchemyIncidenteAreaRepository,
)
from app.infrastructure.adapters.sql_incident_repository import SqlIncidentRepository


def get_incidente_area_service() -> IncidenteAreaService:
    return IncidenteAreaService(
        repo=SqlAlchemyIncidenteAreaRepository(),
        area_repo=SqlAlchemyAreaInhabilitadaRepository(),
        incident_repo=SqlIncidentRepository(),
    )
