"""Adaptador SQLAlchemy para persistencia de archivos subidos."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.file_repository import FileRepositoryPort
from app.core.config import settings
from app.infrastructure.database.models import FileModel


def _get_session() -> Session:
    """Crea una sesión síncrona nueva para cada operación."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@dataclass
class FileData:
    """Datos de un archivo."""
    id: UUID
    url: str
    file_type: str | None
    uploaded_by_user_id: UUID | None


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

    def get_by_id(self, file_id: UUID) -> FileData | None:
        """Obtiene un archivo por su ID."""
        db = _get_session()
        try:
            stmt = select(FileModel).where(FileModel.id == file_id)
            model = db.scalar(stmt)
            if model:
                return FileData(
                    id=model.id,
                    url=model.url,
                    file_type=model.file_type,
                    uploaded_by_user_id=model.uploaded_by_user_id,
                )
            return None
        finally:
            db.close()
