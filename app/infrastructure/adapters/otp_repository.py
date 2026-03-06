"""Adaptador SQLAlchemy que implementa OtpRepositoryPort."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.otp_repository import OtpRepositoryPort
from app.core.config import settings
from app.domain.entities.otp import Otp
from app.infrastructure.database.models import OtpModel


def _get_session() -> Session:
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _to_entity(model: OtpModel) -> Otp:
    """Convierte OtpModel → entidad de dominio Otp."""
    return Otp(
        id=model.id,
        user_id=model.user_id,
        code=model.code,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )


class SqlOtpRepository(OtpRepositoryPort):
    """Implementación del puerto de OTPs usando SQLAlchemy síncrono."""

    def save(self, otp: Otp) -> Otp:
        """Persiste un nuevo OTP en la base de datos."""
        db = _get_session()
        try:
            model = OtpModel(
                user_id=otp.user_id,
                code=otp.code,
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            return _to_entity(model)
        finally:
            db.close()

    def find_active_by_user_id(self, user_id: UUID) -> Otp | None:
        """Retorna el OTP activo (deleted_at IS NULL) del usuario, o None."""
        db = _get_session()
        try:
            stmt = (
                select(OtpModel)
                .where(OtpModel.user_id == user_id)
                .where(OtpModel.deleted_at.is_(None))
                .order_by(OtpModel.created_at.desc())
                .limit(1)
            )
            model = db.scalar(stmt)
            return _to_entity(model) if model else None
        finally:
            db.close()

    def soft_delete(self, otp_id: UUID) -> None:
        """Marca el OTP como consumido (deleted_at y updated_at = NOW())."""
        db = _get_session()
        try:
            stmt = select(OtpModel).where(OtpModel.id == otp_id)
            model = db.scalar(stmt)
            if model:
                now = datetime.now(UTC)
                model.deleted_at = now
                model.updated_at = now
                db.commit()
        finally:
            db.close()
