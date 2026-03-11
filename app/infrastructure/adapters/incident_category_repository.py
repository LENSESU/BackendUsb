"""Adaptador: repositorio de categorias de incidentes con SQLAlchemy."""

from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.incident_category_repository import (
    IncidentCategoryRepository,
)
from app.core.config import settings
from app.domain.entities.incident_category import IncidentCategory
from app.infrastructure.database.models import IncidentCategoryModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class SqlIncidentCategoryRepository(IncidentCategoryRepository):
    def get_all(self) -> list[IncidentCategory]:
        db = _get_session()
        try:
            rows = db.scalars(select(IncidentCategoryModel)).all()
            return [
                IncidentCategory(id=row.id, name=row.name, description=row.description)
                for row in rows
            ]
        finally:
            db.close()

    def get_by_id(self, category_id: UUID) -> IncidentCategory | None:
        db = _get_session()
        try:
            row = db.scalar(
                select(IncidentCategoryModel).where(
                    IncidentCategoryModel.id == category_id
                )
            )
            if row is None:
                return None
            return IncidentCategory(
                id=row.id, name=row.name, description=row.description
            )
        finally:
            db.close()
