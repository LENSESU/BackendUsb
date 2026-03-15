"""Tests para validación de formato en carga de evidencia de incidentes."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
