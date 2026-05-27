from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.area_inhabilitada_repository import (
    AreaInhabilitadaRepositoryPort,
)
from app.core.config import settings
from app.domain.entities.area_inhabilitada import AreaInhabilitada
from app.infrastructure.database.models import AreaInhabilitadaModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _to_entity(row: AreaInhabilitadaModel) -> AreaInhabilitada:
    return AreaInhabilitada(
        id=row.id,
        nombre=row.nombre,
        motivo=row.motivo,
        fecha_inicio=row.fecha_inicio,
        descripcion=row.descripcion,
        fecha_fin=row.fecha_fin,
        activa=row.activa,
        lugar_campus=row.lugar_campus,
        latitud=float(row.latitude) if row.latitude is not None else None,
        longitud=float(row.longitude) if row.longitude is not None else None,
        registrada_por_id=row.registrada_por_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyAreaInhabilitadaRepository(AreaInhabilitadaRepositoryPort):
    def save(self, area: AreaInhabilitada) -> AreaInhabilitada:
        db = _get_session()
        try:
            row = AreaInhabilitadaModel(
                id=area.id,
                nombre=area.nombre,
                motivo=area.motivo,
                descripcion=area.descripcion,
                fecha_inicio=area.fecha_inicio,
                fecha_fin=area.fecha_fin,
                activa=area.activa,
                lugar_campus=area.lugar_campus,
                latitude=area.latitud,
                longitude=area.longitud,
                registrada_por_id=area.registrada_por_id,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return _to_entity(row)
        finally:
            db.close()

    def find_all(self, solo_activas: bool = False) -> list[AreaInhabilitada]:
        db = _get_session()
        try:
            stmt = select(AreaInhabilitadaModel)
            if solo_activas:
                stmt = stmt.where(AreaInhabilitadaModel.activa.is_(True))
            rows = db.scalars(stmt).all()
            return [_to_entity(r) for r in rows]
        finally:
            db.close()

    def find_by_id(self, area_id: str) -> AreaInhabilitada | None:
        db = _get_session()
        try:
            stmt = select(AreaInhabilitadaModel).where(
                AreaInhabilitadaModel.id == UUID(str(area_id))
            )
            row = db.scalar(stmt)
            if row is None:
                return None
            return _to_entity(row)
        finally:
            db.close()

    def update(self, area: AreaInhabilitada) -> AreaInhabilitada | None:
        db = _get_session()
        try:
            if area.id is None:
                return None
            stmt = select(AreaInhabilitadaModel).where(
                AreaInhabilitadaModel.id == area.id
            )
            row = db.scalar(stmt)
            if row is None:
                return None
            row.nombre = area.nombre
            row.motivo = area.motivo
            row.descripcion = area.descripcion
            row.fecha_inicio = area.fecha_inicio
            row.fecha_fin = area.fecha_fin
            row.activa = area.activa
            row.lugar_campus = area.lugar_campus
            row.latitude = area.latitud
            row.longitude = area.longitud
            from datetime import datetime as dt

            row.updated_at = dt.utcnow()
            db.commit()
            db.refresh(row)
            return _to_entity(row)
        finally:
            db.close()

    def delete(self, area_id: str) -> bool:
        db = _get_session()
        try:
            stmt = select(AreaInhabilitadaModel).where(
                AreaInhabilitadaModel.id == UUID(str(area_id))
            )
            row = db.scalar(stmt)
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()
