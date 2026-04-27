"""Tests para validación de formato en carga de evidencia de incidentes."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_current_role_name
from app.api.dependencies.auth import get_current_user_id
from app.api.dependencies.storage import get_incident_evidence_service
from app.application.ports.file_storage import FileStoragePort, StoredFileResult
from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.domain.entities.incident import Incident
from app.main import app

client = TestClient(app)


class InMemoryIncidentRepository:
    def __init__(self) -> None:
        self._store: dict[UUID, Incident] = {}

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        incident = self._store.get(incident_id)
        if incident is None:
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
            self._store[incident_id] = incident
        return incident

    def save(self, incident: Incident) -> Incident:
        assert incident.id is not None
        self._store[incident.id] = incident
        return incident


class InMemoryFileRepository:
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
    async def upload_incident_evidence(
        self,
        *,
        incident_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        object_name = f"incidents/evidence/{incident_id}/{filename}"
        url = f"https://storage.googleapis.com/test-bucket/{object_name}"
        return StoredFileResult(object_name=object_name, file_url=url)


@pytest.fixture(autouse=True)
def override_evidence_dependencies() -> None:
    incident_repo = InMemoryIncidentRepository()
    file_repo = InMemoryFileRepository()
    storage = FakeStorage()

    def _override_service() -> IncidentEvidenceService:
        return IncidentEvidenceService(
            storage=storage,
            incident_repository=incident_repo,
            file_repository=file_repo,
        )

    app.dependency_overrides[get_current_role_name] = lambda: "Administrator"
    app.dependency_overrides[get_current_user_id] = lambda: uuid4()
    app.dependency_overrides[get_incident_evidence_service] = _override_service
    yield
    app.dependency_overrides.clear()


def test_upload_incident_evidence_accepts_jpeg() -> None:
    incident_id = uuid4()

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        files={"photo": ("evidencia.jpg", b"jpeg-bytes", "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["incident_id"] == str(incident_id)
    assert data["filename"] == "evidencia.jpg"
    assert data["content_type"] == "image/jpeg"


def test_upload_incident_evidence_accepts_png() -> None:
    incident_id = uuid4()

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        files={"photo": ("evidencia.png", b"png-bytes", "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["content_type"] == "image/png"


def test_upload_incident_evidence_rejects_invalid_file_format() -> None:
    incident_id = uuid4()

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        files={"photo": ("archivo.txt", b"text", "text/plain")},
    )

    assert response.status_code == 400
    assert "Formato de archivo no permitido" in response.json()["detail"]


def test_upload_incident_evidence_accepts_file_under_5mb() -> None:
    """Acepta imágenes menores a 5MB."""
    incident_id = uuid4()
    # Archivo de 4MB (dentro del límite)
    file_content = b"x" * (4 * 1024 * 1024)

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        files={"photo": ("grande.jpg", file_content, "image/jpeg")},
    )

    assert response.status_code == 201


def test_upload_incident_evidence_rejects_file_over_5mb() -> None:
    """Rechaza imágenes mayores a 5MB."""
    incident_id = uuid4()
    # Archivo de 6MB (excede el límite)
    file_content = b"x" * (6 * 1024 * 1024)

    response = client.post(
        f"/api/v1/incidents/{incident_id}/evidence",
        files={"photo": ("muy_grande.png", file_content, "image/png")},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "supera el tamaño máximo" in detail
    assert "5MB" in detail
