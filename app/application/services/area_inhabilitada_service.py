from datetime import datetime
from uuid import UUID, uuid4

from app.application.ports.area_inhabilitada_repository import AreaInhabilitadaRepositoryPort
from app.domain.entities.area_inhabilitada import AreaInhabilitada


class AreaInhabilitadaService:
    def __init__(self, repository: AreaInhabilitadaRepositoryPort) -> None:
        self._repository = repository

    def registrar(
        self,
        nombre: str,
        motivo: str,
        fecha_inicio: datetime,
        descripcion: str | None = None,
        fecha_fin: datetime | None = None,
        lugar_campus: str | None = None,
        latitud: float | None = None,
        longitud: float | None = None,
        registrada_por_id: UUID | None = None,
    ) -> AreaInhabilitada:
        area = AreaInhabilitada(
            id=uuid4(),
            nombre=nombre.strip(),
            motivo=motivo.strip(),
            fecha_inicio=fecha_inicio,
            descripcion=descripcion,
            fecha_fin=fecha_fin,
            lugar_campus=lugar_campus,
            latitud=latitud,
            longitud=longitud,
            registrada_por_id=registrada_por_id,
        )
        return self._repository.save(area)

    def listar(self, solo_activas: bool = False) -> list[AreaInhabilitada]:
        return self._repository.find_all(solo_activas=solo_activas)

    def obtener_por_id(self, area_id: str) -> AreaInhabilitada | None:
        return self._repository.find_by_id(area_id)

    def actualizar(
        self,
        area_id: str,
        nombre: str | None = None,
        motivo: str | None = None,
        descripcion: str | None = None,
        fecha_inicio: datetime | None = None,
        fecha_fin: datetime | None = None,
        activa: bool | None = None,
        lugar_campus: str | None = None,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> AreaInhabilitada | None:
        existing = self._repository.find_by_id(area_id)
        if existing is None:
            return None

        nueva_fecha_inicio = fecha_inicio if fecha_inicio is not None else existing.fecha_inicio
        nueva_fecha_fin = fecha_fin if fecha_fin is not None else existing.fecha_fin

        updated = AreaInhabilitada(
            id=existing.id,
            nombre=(nombre.strip() if nombre is not None else existing.nombre),
            motivo=(motivo.strip() if motivo is not None else existing.motivo),
            descripcion=(descripcion if descripcion is not None else existing.descripcion),
            fecha_inicio=nueva_fecha_inicio,
            fecha_fin=nueva_fecha_fin,
            activa=(activa if activa is not None else existing.activa),
            lugar_campus=(lugar_campus if lugar_campus is not None else existing.lugar_campus),
            latitud=(latitud if latitud is not None else existing.latitud),
            longitud=(longitud if longitud is not None else existing.longitud),
            registrada_por_id=existing.registrada_por_id,
        )
        return self._repository.update(updated)

    def eliminar(self, area_id: str) -> bool:
        return self._repository.delete(area_id)
