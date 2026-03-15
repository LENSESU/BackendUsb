from pathlib import Path
from uuid import UUID, uuid4

from app.application.ports.file_storage import FileStoragePort, StoredFileResult


class InMemoryFileStorageAdapter(FileStoragePort):
    """Adaptador simple para desarrollo/tests sin proveedor externo."""

    async def upload_incident_evidence(
        self,
        *,
        incident_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        extension = Path(filename).suffix.lower() or ".jpg"
        object_name = f"incidents/{incident_id}/{uuid4().hex}{extension}"
        return StoredFileResult(object_name=object_name, file_url=None)
