"""Tests de aplicación: persistencia de URL y asociación al incidente.

Estos tests validan que:
 - La URL devuelta por el almacenamiento se guarda como un "archivo" persistido.
 - El incidente queda asociado a ese archivo mediante before_photo_id.

Se usan dobles de prueba en memoria para no depender de la base de datos real
ni de Google Cloud Storage.
"""

from uuid import UUID, uuid4

from app.application.ports.file_repository import FileRepositoryPort
from app.application.ports.file_storage import FileStoragePort, StoredFileResult
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.domain.entities.incident import Incident


class InMemoryIncidentRepository(IncidentRepositoryPort):
    """Repositorio de incidentes en memoria para pruebas."""

    def __init__(self) -> None:
        self._store: dict[UUID, Incident] = {}

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        return self._store.get(incident_id)

    def list_all(self) -> list[Incident]:
        return list(self._store.values())

    def save(self, incident: Incident) -> Incident:
        assert incident.id is not None
        self._store[incident.id] = incident
        return incident

    def delete(self, incident_id: UUID) -> bool:
        return self._store.pop(incident_id, None) is not None


class InMemoryFileRepository(FileRepositoryPort):
    """Repositorio de archivos en memoria para pruebas."""

    def __init__(self) -> None:
        self.created_files: dict[UUID, tuple[str, str | None, UUID | None]] = {}

    def create_file(
        self,
        *,
        url: str,
        file_type: str | None,
        uploaded_by_user_id: UUID | None,
    ) -> UUID:
        file_id = uuid4()
        self.created_files[file_id] = (url, file_type, uploaded_by_user_id)
        return file_id


class FakeStorage(FileStoragePort):
    """Adaptador de almacenamiento simulado que siempre devuelve una URL."""

    async def upload_incident_evidence(
        self,
        *,
        incident_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        # Generamos una URL determinista en función del ID para aserciones.
        url = f"https://storage.test/incidents/{incident_id}/{filename}"
        object_name = f"incidents/{incident_id}/{filename}"
        return StoredFileResult(object_name=object_name, file_url=url)


async def test_upload_evidence_persists_file_and_links_incident(mocker) -> None:
    """La evidencia se sube, se guarda su URL y se asocia al incidente."""
    # Preparar incidente existente en el repositorio en memoria.
    incident_repo = InMemoryIncidentRepository()
    file_repo = InMemoryFileRepository()
    storage = FakeStorage()

    incident_id = uuid4()
    incident = Incident(
        id=incident_id,
        student_id=uuid4(),
        technician_id=None,
        category_id=uuid4(),
        description="Incidente de prueba",
        status="Nuevo",
        priority=None,
        before_photo_id=None,
        after_photo_id=None,
        created_at=None,
        updated_at=None,
        location=None,
    )
    incident_repo.save(incident)

    service = IncidentEvidenceService(
        storage=storage,
        incident_repository=incident_repo,
        file_repository=file_repo,
    )

    # Simular un UploadFile con contenido pequeño.
    upload_file = mocker.Mock()
    upload_file.filename = "evidencia.jpg"
    upload_file.content_type = "image/jpeg"
    upload_file.read = mocker.AsyncMock(return_value=b"fake-bytes")

    # Evitar que la validación de tamaño/formato lea realmente el archivo.
    from app.application.services.file_validation_service import FileValidationService

    mocker.patch.object(
        FileValidationService,
        "validate_incident_evidence_image",
        new=mocker.AsyncMock(return_value=None),
    )

    stored = await service.upload_evidence(incident_id=incident_id, file=upload_file)

    # La URL devuelta por el storage debe coincidir con la usada para crear el archivo.
    assert stored.file_url is not None
    assert len(file_repo.created_files) == 1
    (created_file_id, (created_url, created_type, _)) = next(
        iter(file_repo.created_files.items())
    )
    assert created_url == stored.file_url
    assert created_type == "image/jpeg"

    # El incidente debe quedar enlazado al archivo mediante before_photo_id.
    updated_incident = incident_repo.get_by_id(incident_id)
    assert updated_incident is not None
    assert updated_incident.before_photo_id == created_file_id

