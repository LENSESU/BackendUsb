from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from fastapi.concurrency import run_in_threadpool
from google.cloud import storage

from app.application.ports.file_storage import FileStoragePort, StoredFileResult


class GoogleCloudStorageAdapter(FileStoragePort):
    """Adaptador GCS para almacenar imágenes de evidencia."""

    def __init__(
        self,
        *,
        bucket_name: str,
        project_id: str | None = None,
        evidence_prefix: str = "incidents/evidence",
        make_public: bool = False,
    ) -> None:
        self._bucket_name = bucket_name
        self._evidence_prefix = evidence_prefix.strip("/")
        self._make_public = make_public

        # ADC: usa credenciales del entorno sin credenciales (JSON) en el proyecto.
        self._client = storage.Client(project=project_id)

        self._bucket = self._client.bucket(bucket_name)

    async def upload_incident_evidence(
        self,
        *,
        incident_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        extension = Path(filename).suffix.lower() or ".jpg"
        now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        object_name = (
            f"{self._evidence_prefix}/incidents/{incident_id}/{now}-{uuid4().hex}{extension}"
        )

        return await run_in_threadpool(
            self._upload_blocking,
            object_name,
            content_type,
            data,
        )

    def _upload_blocking(
        self,
        object_name: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        blob = self._bucket.blob(object_name)
        blob.upload_from_string(data, content_type=content_type)

        file_url = f"gs://{self._bucket_name}/{object_name}"
        if self._make_public:
            blob.make_public()
            file_url = blob.public_url

        return StoredFileResult(object_name=object_name, file_url=file_url)
