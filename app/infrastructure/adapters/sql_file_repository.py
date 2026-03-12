"""Adaptador SQLAlchemy que implementa FileRepositoryPort."""

from uuid import UUID

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.ports.file_repository import FileRepositoryPort
from app.core.config import settings
from app.domain.entities.file_resource import FileResource
from app.infrastructure.database.models import FileModel


def _get_session() -> Session:
    """Crea una sesión síncrona contra la base de datos."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _to_entity(model: FileModel) -> FileResource:
    """Convierte FileModel → entidad de dominio FileResource."""
    return FileResource(
        id=model.id,
        url=model.url,
        file_type=model.file_type,
        uploaded_by_user_id=model.uploaded_by_user_id,
        created_at=model.created_at,
    )


class SqlFileRepository(FileRepositoryPort):
    """Implementación del puerto de archivos usando SQLAlchemy síncrono."""

    def create(self, file: FileResource) -> FileResource:
        """Persiste un nuevo archivo (URL de GCS, etc.) y retorna la entidad con id."""
        db = _get_session()
        try:
            model = FileModel(
                url=file.url,
                file_type=file.file_type,
                uploaded_by_user_id=file.uploaded_by_user_id,
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            return _to_entity(model)
        finally:
            db.close()

    def get_by_id(self, file_id: UUID) -> FileResource | None:
        """Obtiene un archivo por su ID, o None si no existe."""
        db = _get_session()
        try:
            stmt = select(FileModel).where(FileModel.id == file_id)
            model = db.scalar(stmt)
            return _to_entity(model) if model else None
        finally:
            db.close()
