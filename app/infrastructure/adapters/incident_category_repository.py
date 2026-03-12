from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.incident_category_repository import (
    IncidentCategoryRepositoryPort,
)
from app.core.config import settings
from app.domain.entities.incident_category import IncidentCategory
from app.infrastructure.database.models import IncidentCategoryModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class SqlAlchemyIncidentCategoryRepository(IncidentCategoryRepositoryPort):
    def save(self, category: IncidentCategory) -> IncidentCategory:
        db = _get_session()
        try:
            row = IncidentCategoryModel(
                name=category.name, description=
                category.description)
            db.add(row)
            db.commit()
            db.refresh(row)
            return IncidentCategory(
                id=row.id, name=row.name, description=row.description)
        finally:
            db.close()

    def find_by_name(self, name: str) -> IncidentCategory | None:
        db = _get_session()
        try:
            stmt = select(IncidentCategoryModel).where(
                IncidentCategoryModel.name == name)
            row = db.scalar(stmt)
            if row is None:
                return None
            return IncidentCategory(
                id=row.id, name=row.name, description=row.description)
        finally:
            db.close()

    def find_all(self) -> list[IncidentCategory]:
        db = _get_session()
        try:
            stmt = select(IncidentCategoryModel)
            rows = db.scalars(stmt).all()
            return [
                IncidentCategory(id=r.id, name=r.name, description=r.description)
                for r in rows
            ]
        finally:
            db.close()

    def find_by_id(self, category_id: str) -> IncidentCategory | None:
        db = _get_session()
        try:
            stmt = select(IncidentCategoryModel).where(
                IncidentCategoryModel.id == UUID(str(category_id))
            )
            row = db.scalar(stmt)
            if row is None:
                return None
            return IncidentCategory(
                id=row.id, name=row.name, description=row.description)
        finally:
            db.close()

    def get_by_id(self, category_id: UUID) -> IncidentCategory | None:
        return self.find_by_id(str(category_id))