# app/application/services/area_inhabilitada_service.py
from datetime import datetime
from uuid import UUID, uuid4

from app.application.ports.area_inhabilitada_repository import (
    AreaInhabilitadaRepositoryPort,
)
from app.domain.entities.area_inhabilitada import AreaInhabilitada

_UNSET: object = object()


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
            registrada_por_id=registrada_por_id,  # ← persiste el autor
        )
        return self._repository.save(area)

    def listar(self, solo_activas: bool = False) -> list[AreaInhabilitada]:
        return self._repository.find_all(solo_activas=solo_activas)

    def listar_por_lugar(self, lugar_campus: str) -> list[AreaInhabilitada]:
        """Retorna áreas activas filtradas por lugar del campus."""
        return self._repository.find_by_lugar_campus(lugar_campus)

    def obtener_por_id(self, area_id: str) -> AreaInhabilitada | None:
        return self._repository.find_by_id(area_id)

    def actualizar(
        self,
        area_id: str,
        solicitante_id: UUID | None = None,  # ← NUEVO: para validar ownership
        es_admin: bool = False,  # ← NUEVO: admin bypasea la validación
        nombre: str | None = _UNSET,  # type: ignore[assignment]
        motivo: str | None = _UNSET,  # type: ignore[assignment]
        descripcion: str | None = _UNSET,  # type: ignore[assignment]
        fecha_inicio: datetime | None = _UNSET,  # type: ignore[assignment]
        fecha_fin: datetime | None = _UNSET,  # type: ignore[assignment]
        activa: bool | None = _UNSET,  # type: ignore[assignment]
        lugar_campus: str | None = _UNSET,  # type: ignore[assignment]
        latitud: float | None = _UNSET,  # type: ignore[assignment]
        longitud: float | None = _UNSET,  # type: ignore[assignment]
    ) -> AreaInhabilitada | None:
        existing = self._repository.find_by_id(area_id)
        if existing is None:
            return None

        # Técnico solo puede editar áreas que él registró
        if not es_admin and solicitante_id is not None:
            if existing.registrada_por_id != solicitante_id:
                raise PermissionError(
                    "Solo el técnico que registró el área puede modificarla."
                )

        updated = AreaInhabilitada(
            id=existing.id,
            nombre=(
                nombre.strip()
                if nombre is not _UNSET and nombre is not None
                else existing.nombre
            ),
            motivo=(
                motivo.strip()
                if motivo is not _UNSET and motivo is not None
                else existing.motivo
            ),
            descripcion=(
                descripcion if descripcion is not _UNSET else existing.descripcion
            ),
            fecha_inicio=(
                fecha_inicio
                if fecha_inicio is not _UNSET and fecha_inicio is not None
                else existing.fecha_inicio
            ),
            fecha_fin=(fecha_fin if fecha_fin is not _UNSET else existing.fecha_fin),
            activa=(
                activa
                if activa is not _UNSET and activa is not None
                else existing.activa
            ),
            lugar_campus=(
                lugar_campus if lugar_campus is not _UNSET else existing.lugar_campus
            ),
            latitud=(latitud if latitud is not _UNSET else existing.latitud),
            longitud=(longitud if longitud is not _UNSET else existing.longitud),
            registrada_por_id=existing.registrada_por_id,
        )
        return self._repository.update(updated)

    def eliminar(self, area_id: str) -> bool:
        return self._repository.delete(area_id)
