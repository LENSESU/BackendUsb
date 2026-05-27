from uuid import UUID

from app.application.ports.area_inhabilitada_repository import (
    AreaInhabilitadaRepositoryPort,
)
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.ports.incidente_area_repository import IncidenteAreaRepositoryPort
from app.domain.entities.area_inhabilitada import AreaInhabilitada
from app.domain.entities.incident import Incident


class IncidenteAreaService:
    def __init__(
        self,
        repo: IncidenteAreaRepositoryPort,
        area_repo: AreaInhabilitadaRepositoryPort,
        incident_repo: IncidentRepositoryPort,
    ) -> None:
        self._repo = repo
        self._area_repo = area_repo
        self._incident_repo = incident_repo

    def asociar(self, incidente_id: UUID, area_id: UUID) -> None:
        if self._incident_repo.get_by_id(incidente_id) is None:
            raise ValueError(f"Incidente con id {incidente_id} no encontrado.")
        if self._area_repo.find_by_id(str(area_id)) is None:
            raise ValueError(f"Área inhabilitada con id {area_id} no encontrada.")
        if self._repo.existe(incidente_id, area_id):
            raise ValueError("El incidente ya está asociado a esta área inhabilitada.")
        self._repo.asociar(incidente_id, area_id)

    def desasociar(self, incidente_id: UUID, area_id: UUID) -> bool:
        return self._repo.desasociar(incidente_id, area_id)

    def obtener_incidentes_por_area(self, area_id: UUID) -> list[Incident]:
        ids = self._repo.listar_incidente_ids_por_area(area_id)
        result = []
        for iid in ids:
            incident = self._incident_repo.get_by_id(iid)
            if incident is not None:
                result.append(incident)
        return result

    def obtener_areas_por_incidente(self, incidente_id: UUID) -> list[AreaInhabilitada]:
        ids = self._repo.listar_area_ids_por_incidente(incidente_id)
        result = []
        for aid in ids:
            area = self._area_repo.find_by_id(str(aid))
            if area is not None:
                result.append(area)
        return result
