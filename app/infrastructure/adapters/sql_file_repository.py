"""Adaptador SQLAlchemy para persistencia de archivos subidos."""

from uuid import UUID

from sqlalchemy.orm import Session
from app.infrastructure.db import SyncSessionLocal

from app.application.ports.file_repository import FileRepositoryPort
from app.infrastructure.database.models import FileModel


def _get_session() -> Session:
    return SyncSessionLocal()


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
