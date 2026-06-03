from abc import ABC, abstractmethod

from app.domain.entities.area_inhabilitada import AreaInhabilitada


class AreaInhabilitadaRepositoryPort(ABC):
    @abstractmethod
    def save(self, area: AreaInhabilitada) -> AreaInhabilitada: ...

    @abstractmethod
    def find_all(self, solo_activas: bool = False) -> list[AreaInhabilitada]: ...

    @abstractmethod
    def find_by_id(self, area_id: str) -> AreaInhabilitada | None: ...

    @abstractmethod
    def update(self, area: AreaInhabilitada) -> AreaInhabilitada | None: ...

    @abstractmethod
    def delete(self, area_id: str) -> bool: ...

    @abstractmethod
    def find_by_lugar_campus(self, lugar_campus: str) -> list[AreaInhabilitada]: ...
