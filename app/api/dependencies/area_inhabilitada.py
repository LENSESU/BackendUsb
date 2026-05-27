from app.application.services.area_inhabilitada_service import AreaInhabilitadaService
from app.infrastructure.adapters.area_inhabilitada_repository import (
    SqlAlchemyAreaInhabilitadaRepository,
)


def get_area_inhabilitada_service() -> AreaInhabilitadaService:
    return AreaInhabilitadaService(repository=SqlAlchemyAreaInhabilitadaRepository())
