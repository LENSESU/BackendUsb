"""Adaptador SQLAlchemy que implementa SuggestionRepositoryPort."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.domain.entities.suggestion import Suggestion
from app.infrastructure.database.models import (
    SuggestionModel,
    SuggestionTagModel,
    TagModel,
)
from app.infrastructure.db import SyncSessionLocal


def _get_session() -> Session:
    return SyncSessionLocal()


def _get_tag_names_for_suggestion(db: Session, suggestion_id: UUID) -> list[str]:
    """Obtiene los nombres de todas las etiquetas asociadas a una sugerencia."""
    stmt = (
        select(TagModel.name)
        .join(SuggestionTagModel, SuggestionTagModel.tag_id == TagModel.id)
        .where(SuggestionTagModel.suggestion_id == suggestion_id)
        .order_by(TagModel.name)
    )
    return [row for row in db.scalars(stmt).all()]


def _model_to_entity(
    model: SuggestionModel, tag_names: list[str] | None = None
) -> Suggestion:
    return Suggestion(
        id=model.id,
        student_id=model.student_id,
        title=model.title,
        content=model.content,
        photo_id=model.photo_id,
        total_votes=model.total_votes,
        institutional_comment=model.institutional_comment,
        created_at=model.created_at,
        tags=tag_names or [],
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
            if not model:
                return None
            tag_names = _get_tag_names_for_suggestion(db, suggestion_id)
            return _model_to_entity(model, tag_names)
        finally:
            db.close()

    def list_all(self) -> list[Suggestion]:
        db = _get_session()
        try:
            stmt = select(SuggestionModel).order_by(SuggestionModel.created_at.desc())
            rows = db.scalars(stmt).all()
            return [
                _model_to_entity(m, _get_tag_names_for_suggestion(db, m.id))
                for m in rows
            ]
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
            return [
                _model_to_entity(m, _get_tag_names_for_suggestion(db, m.id))
                for m in rows
            ]
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
                tag_names = _get_tag_names_for_suggestion(db, existing.id)
                return _model_to_entity(existing, tag_names)
            model = _entity_to_model(suggestion, None)
            db.add(model)
            db.commit()
            db.refresh(model)
            return _model_to_entity(model, [])
        finally:
            db.close()

    def save_with_tags(
        self, suggestion: Suggestion, tag_names: list[str] | None = None
    ) -> Suggestion:
        """Guarda sugerencia y asocia etiquetas (crea las que no existan)."""
        db = _get_session()
        try:
            if suggestion.id is None:
                msg = "La sugerencia debe tener id antes de guardar"
                raise ValueError(msg)

            # Guardar sugerencia
            stmt = select(SuggestionModel).where(SuggestionModel.id == suggestion.id)
            existing = db.scalar(stmt)
            if existing:
                _entity_to_model(suggestion, existing)
                db.commit()
                db.refresh(existing)
                model = existing
            else:
                model = _entity_to_model(suggestion, None)
                db.add(model)
                db.commit()
                db.refresh(model)

            # Procesar etiquetas
            resolved_tags = []
            if tag_names:
                for tag_name in tag_names:
                    tag_name = tag_name.strip().lower()
                    if not tag_name:
                        continue

                    # Buscar o crear etiqueta
                    tag_stmt = select(TagModel).where(TagModel.name == tag_name)
                    tag = db.scalar(tag_stmt)
                    if not tag:
                        tag = TagModel(name=tag_name)
                        db.add(tag)
                        db.flush()

                    # Crear asociación si no existe
                    assoc_stmt = select(SuggestionTagModel).where(
                        SuggestionTagModel.suggestion_id == model.id,
                        SuggestionTagModel.tag_id == tag.id,
                    )
                    if not db.scalar(assoc_stmt):
                        assoc = SuggestionTagModel(
                            suggestion_id=model.id,
                            tag_id=tag.id,
                        )
                        db.add(assoc)

                    resolved_tags.append(tag_name)

                db.commit()

            return _model_to_entity(model, resolved_tags)
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
