from abc import ABC, abstractmethod
from uuid import UUID


class IncidenteAreaRepositoryPort(ABC):
    @abstractmethod
    def asociar(self, incidente_id: UUID, area_id: UUID) -> None: ...

    @abstractmethod
    def desasociar(self, incidente_id: UUID, area_id: UUID) -> bool: ...

    @abstractmethod
    def existe(self, incidente_id: UUID, area_id: UUID) -> bool: ...

    @abstractmethod
    def listar_incidente_ids_por_area(self, area_id: UUID) -> list[UUID]: ...

    @abstractmethod
    def listar_area_ids_por_incidente(self, incidente_id: UUID) -> list[UUID]: ...
