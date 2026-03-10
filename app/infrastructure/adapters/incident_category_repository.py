"""Adaptador SQLAlchemy para categorías de incidentes."""

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


def _to_entity(model: IncidentCategoryModel) -> IncidentCategory:
    return IncidentCategory(
        id=model.id,
        name=model.name,
        description=model.description,
    )


class SqlIncidentCategoryRepository(IncidentCategoryRepositoryPort):
    """Implementación del puerto de categorías usando SQLAlchemy síncrono."""

    def save(self, category: IncidentCategory) -> IncidentCategory:
        db = _get_session()
        try:
            model = IncidentCategoryModel(
                name=category.name,
                description=category.description,
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            return _to_entity(model)
        finally:
            db.close()

    def find_by_name(self, name: str) -> IncidentCategory | None:
        db = _get_session()
        try:
            stmt = select(IncidentCategoryModel).where(
                IncidentCategoryModel.name.ilike(name)
            )
            model = db.scalar(stmt)
            return _to_entity(model) if model else None
        finally:
            db.close()

    def find_all(self) -> list[IncidentCategory]:
        db = _get_session()
        try:
            stmt = select(IncidentCategoryModel).order_by(IncidentCategoryModel.name)
            models = db.scalars(stmt).all()
            return [_to_entity(m) for m in models]
        finally:
            db.close()
