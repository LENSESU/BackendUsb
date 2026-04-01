"""Adaptador SQLAlchemy que implementa SuggestionRepositoryPort."""

from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.core.config import settings
from app.domain.entities.suggestion import Suggestion
from app.infrastructure.database.models import SuggestionModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _model_to_entity(model: SuggestionModel) -> Suggestion:
    return Suggestion(
        id=model.id,
        student_id=model.student_id,
        title=model.title,
        content=model.content,
        photo_id=model.photo_id,
        total_votes=model.total_votes,
        institutional_comment=model.institutional_comment,
        created_at=model.created_at,
    )


def _entity_to_model(
    suggestion: Suggestion, existing: SuggestionModel | None = None
) -> SuggestionModel:
    if existing is not None:
        existing.student_id = suggestion.student_id
        existing.title = suggestion.title
        existing.content = suggestion.content
        existing.photo_id = suggestion.photo_id
        existing.total_votes = suggestion.total_votes
        existing.institutional_comment = suggestion.institutional_comment
        return existing

    return SuggestionModel(
        id=suggestion.id,
        student_id=suggestion.student_id,
        title=suggestion.title,
        content=suggestion.content,
        photo_id=suggestion.photo_id,
        total_votes=suggestion.total_votes,
        institutional_comment=suggestion.institutional_comment,
    )


class SqlSuggestionRepository(SuggestionRepositoryPort):
    """Implementación del puerto de sugerencias usando SQLAlchemy síncrono."""

    def get_by_id(self, suggestion_id: UUID) -> Suggestion | None:
        db = _get_session()
        try:
            stmt = select(SuggestionModel).where(SuggestionModel.id == suggestion_id)
            model = db.scalar(stmt)
            return _model_to_entity(model) if model else None
        finally:
            db.close()

    def list_all(self) -> list[Suggestion]:
        db = _get_session()
        try:
            stmt = select(SuggestionModel).order_by(SuggestionModel.created_at.desc())
            rows = db.scalars(stmt).all()
            return [_model_to_entity(m) for m in rows]
        finally:
            db.close()

    def list_popular(self, limit: int) -> list[Suggestion]:
        db = _get_session()
        try:
            stmt = (
                select(SuggestionModel)
                .order_by(
                    SuggestionModel.total_votes.desc(),
                    SuggestionModel.created_at.desc(),
                )
                .limit(limit)
            )
            rows = db.scalars(stmt).all()
            return [_model_to_entity(m) for m in rows]
        finally:
            db.close()

    def save(self, suggestion: Suggestion) -> Suggestion:
        db = _get_session()
        try:
            if suggestion.id is None:
                msg = "La sugerencia debe tener id antes de guardar"
                raise ValueError(msg)
            stmt = select(SuggestionModel).where(SuggestionModel.id == suggestion.id)
            existing = db.scalar(stmt)
            if existing:
                _entity_to_model(suggestion, existing)
                db.commit()
                db.refresh(existing)
                return _model_to_entity(existing)
            model = _entity_to_model(suggestion, None)
            db.add(model)
            db.commit()
            db.refresh(model)
            return _model_to_entity(model)
        finally:
            db.close()

    def delete(self, suggestion_id: UUID) -> bool:
        db = _get_session()
        try:
            stmt = select(SuggestionModel).where(SuggestionModel.id == suggestion_id)
            model = db.scalar(stmt)
            if model is None:
                return False
            db.delete(model)
            db.commit()
            return True
        finally:
            db.close()
