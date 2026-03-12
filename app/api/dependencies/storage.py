from functools import lru_cache

from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.core.config import settings
from app.infrastructure.adapters.gcs_file_storage import GoogleCloudStorageAdapter
from app.infrastructure.adapters.in_memory_file_storage import (
    InMemoryFileStorageAdapter,
)
from app.infrastructure.adapters.sql_file_repository import SqlFileRepository
from app.infrastructure.adapters.sql_incident_repository import SqlIncidentRepository


@lru_cache
def get_incident_evidence_service() -> IncidentEvidenceService:
    """Construye el servicio de evidencia con storage y repositorios."""
    if settings.gcs_enabled:
        if not settings.gcs_bucket_name:
            raise ValueError("GCS_BUCKET_NAME es obligatorio cuando GCS_ENABLED=true")

        storage_adapter = GoogleCloudStorageAdapter(
            bucket_name=settings.gcs_bucket_name,
            project_id=settings.gcs_project_id,
            evidence_prefix=settings.gcs_evidence_prefix,
            make_public=settings.gcs_make_public,
        )
    else:
        storage_adapter = InMemoryFileStorageAdapter()

    file_repository = SqlFileRepository()
    incident_repository = SqlIncidentRepository()

    return IncidentEvidenceService(
        storage=storage_adapter,
        file_repository=file_repository,
        incident_repository=incident_repository,
    )
