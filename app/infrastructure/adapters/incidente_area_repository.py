from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.incidente_area_repository import IncidenteAreaRepositoryPort
from app.core.config import settings
from app.infrastructure.database.models import IncidenteAreaInhabilitadaModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class SqlAlchemyIncidenteAreaRepository(IncidenteAreaRepositoryPort):
    def asociar(self, incidente_id: UUID, area_id: UUID) -> None:
        db = _get_session()
        try:
            row = IncidenteAreaInhabilitadaModel(
                incidente_id=incidente_id,
                area_inhabilitada_id=area_id,
            )
            db.add(row)
            db.commit()
        finally:
            db.close()

    def desasociar(self, incidente_id: UUID, area_id: UUID) -> bool:
        db = _get_session()
        try:
            stmt = select(IncidenteAreaInhabilitadaModel).where(
                IncidenteAreaInhabilitadaModel.incidente_id == incidente_id,
                IncidenteAreaInhabilitadaModel.area_inhabilitada_id == area_id,
            )
            row = db.scalar(stmt)
            if row is None:
                return False
            db.delete(row)
            db.commit()
            return True
        finally:
            db.close()

    def existe(self, incidente_id: UUID, area_id: UUID) -> bool:
        db = _get_session()
        try:
            stmt = select(IncidenteAreaInhabilitadaModel).where(
                IncidenteAreaInhabilitadaModel.incidente_id == incidente_id,
                IncidenteAreaInhabilitadaModel.area_inhabilitada_id == area_id,
            )
            return db.scalar(stmt) is not None
        finally:
            db.close()

    def listar_incidente_ids_por_area(self, area_id: UUID) -> list[UUID]:
        db = _get_session()
        try:
            stmt = select(IncidenteAreaInhabilitadaModel.incidente_id).where(
                IncidenteAreaInhabilitadaModel.area_inhabilitada_id == area_id
            )
            return list(db.scalars(stmt).all())
        finally:
            db.close()

    def listar_area_ids_por_incidente(self, incidente_id: UUID) -> list[UUID]:
        db = _get_session()
        try:
            stmt = select(IncidenteAreaInhabilitadaModel.area_inhabilitada_id).where(
                IncidenteAreaInhabilitadaModel.incidente_id == incidente_id
            )
            return list(db.scalars(stmt).all())
        finally:
            db.close()
