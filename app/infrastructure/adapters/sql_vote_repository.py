"""Adaptador SQLAlchemy que implementa VoteRepositoryPort."""

from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.vote_repository import VoteRepositoryPort
from app.core.config import settings
from app.domain.entities.vote import Vote
from app.infrastructure.database.models import VoteModel
from app.infrastructure.db import SyncSessionLocal


def _get_session() -> Session:
    return SyncSessionLocal()


def _model_to_entity(model: VoteModel) -> Vote:
    return Vote(
        id=model.id,
        student_id=model.student_id,
        suggestion_id=model.suggestion_id,
        created_at=model.created_at,
    )


class SqlVoteRepository(VoteRepositoryPort):
    """Implementación del puerto de Votos usando SQLAlchemy síncrono."""

    def get_by_student_and_suggestion(
        self, student_id: UUID, suggestion_id: UUID
    ) -> Vote | None:
        db = _get_session()
        try:
            stmt = select(VoteModel).where(
                VoteModel.student_id == student_id,
                VoteModel.suggestion_id == suggestion_id,
            )
            model = db.scalar(stmt)
            return _model_to_entity(model) if model else None
        finally:
            db.close()

    def save(self, vote: Vote) -> Vote:
        db = _get_session()
        try:
            model = VoteModel(
                id=vote.id,
                student_id=vote.student_id,
                suggestion_id=vote.suggestion_id,
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            return _model_to_entity(model)
        finally:
            db.close()
