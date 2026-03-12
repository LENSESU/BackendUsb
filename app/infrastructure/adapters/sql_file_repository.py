"""Adaptador SQLAlchemy para persistencia de archivos subidos."""

from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.file_repository import FileRepositoryPort
from app.core.config import settings
from app.infrastructure.database.models import FileModel


def _get_session() -> Session:
    """Crea una sesión síncrona nueva para cada operación."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class SqlFileRepository(FileRepositoryPort):
    """Implementación del puerto de archivos usando SQLAlchemy síncrono."""

    def create_file(
        self,
        *,
        url: str,
        file_type: str | None,
        uploaded_by_user_id: UUID | None,
    ) -> UUID:
        db = _get_session()
        try:
            file_model = FileModel(
                url=url,
                file_type=file_type,
                uploaded_by_user_id=uploaded_by_user_id,
            )
            db.add(file_model)
            db.commit()
            db.refresh(file_model)
            return file_model.id
        finally:
            db.close()

