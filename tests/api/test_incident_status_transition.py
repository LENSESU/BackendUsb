"""Tests del endpoint PATCH /api/v1/incidents/{id}/status.

Valida:
- Solo Administrator y Technician pueden cambiar estado (Student → 403).
- Sin token → 401; token inválido → 401.
- Technician solo puede cambiar el estado de incidentes asignados a él.
- Transiciones válidas: Nuevo → En_proceso → Resuelto.
- Transiciones inválidas (salto, reversa, estado final) → 422 con error_code.
- Estado desconocido → 422.
- Incidente inexistente → 404.
- La respuesta refleja el nuevo estado.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.domain.entities.incident import Incident, IncidentStatus
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)
from app.main import app

client = TestClient(app)

ADMIN_ID = uuid4()
TECH_ID = uuid4()
OTHER_TECH_ID = uuid4()
STUDENT_ID = uuid4()
CATEGORY_ID = uuid4()

_URL = "/api/v1/incidents/{}/status"


def _make_token(user_id, role_name: str) -> str:
    return create_access_token(
        data={
            "sub": str(user_id),
            "email": f"user-{user_id}@usb.ve",
            "role_id": str(uuid4()),
            "role_name": role_name,
        }
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed(
    repo: InMemoryIncidentRepository,
    *,
    status: str = IncidentStatus.NUEVO,
    technician_id=None,
    student_id=None,
) -> Incident:
    incident = Incident(
        id=uuid4(),
        student_id=student_id or STUDENT_ID,
        technician_id=technician_id,
        category_id=CATEGORY_ID,
        description="Luminaria dañada",
        status=status,
        created_at=datetime.now(UTC),
    )
    repo.save(incident)
    return incident


@pytest.fixture(autouse=True)
def _clean():
    import app.api.dependencies.incident as incident_deps

    incident_deps._repository = InMemoryIncidentRepository()
    incident_deps._category_repository = None
    incident_deps._user_repository = None
    clear_blacklist()
    yield
    clear_blacklist()
    incident_deps.reset_incident_dependencies()


def _repo() -> InMemoryIncidentRepository:
    import app.api.dependencies.incident as incident_deps

    return incident_deps._repository  # type: ignore[return-value]


# ── Acceso por rol ────────────────────────────────────────────────────────────


class TestStatusEndpointAccess:
    def test_no_token_returns_401(self):
        inc = _seed(_repo())
        resp = client.patch(_URL.format(inc.id), json={"status": "En_proceso"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self):
        inc = _seed(_repo())
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth("not.a.jwt"),
        )
        assert resp.status_code == 401

    def test_student_returns_403(self):
        inc = _seed(_repo())
        token = _make_token(STUDENT_ID, "Student")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 403

    def test_administrator_can_change_any_incident(self):
        inc = _seed(_repo())
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    def test_technician_assigned_can_change_status(self):
        inc = _seed(_repo(), technician_id=TECH_ID)
        token = _make_token(TECH_ID, "Technician")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

    def test_technician_not_assigned_returns_403(self):
        inc = _seed(_repo(), technician_id=OTHER_TECH_ID)
        token = _make_token(TECH_ID, "Technician")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 403
        assert resp.json()["detail"]["error_code"] == "INCIDENT_STATUS_NOT_ASSIGNED"

    def test_technician_unassigned_incident_returns_403(self):
        inc = _seed(_repo(), technician_id=None)
        token = _make_token(TECH_ID, "Technician")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 403


# ── Transiciones válidas ──────────────────────────────────────────────────────


class TestValidTransitions:
    def test_nuevo_to_en_proceso(self):
        inc = _seed(_repo(), status=IncidentStatus.NUEVO)
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "En_proceso"

    def test_en_proceso_to_resuelto(self):
        inc = _seed(_repo(), status=IncidentStatus.EN_PROCESO)
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "Resuelto"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Resuelto"

    def test_full_lifecycle(self):
        inc = _seed(_repo(), technician_id=TECH_ID)
        token = _make_token(TECH_ID, "Technician")

        r1 = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert r1.status_code == 200
        assert r1.json()["status"] == "En_proceso"

        r2 = client.patch(
            _URL.format(inc.id),
            json={"status": "Resuelto"},
            headers=_auth(token),
        )
        assert r2.status_code == 200
        assert r2.json()["status"] == "Resuelto"

    def test_response_contains_incident_fields(self):
        inc = _seed(_repo())
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        body = resp.json()
        assert body["id"] == str(inc.id)
        assert body["status"] == "En_proceso"
        assert "category_id" in body


# ── Transiciones inválidas ────────────────────────────────────────────────────


class TestInvalidTransitions:
    def test_skip_nuevo_to_resuelto_returns_422(self):
        inc = _seed(_repo(), status=IncidentStatus.NUEVO)
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "Resuelto"},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        error_code = resp.json()["detail"]["error_code"]
        assert error_code == "INCIDENT_STATUS_TRANSITION_INVALID"

    def test_backwards_en_proceso_to_nuevo_returns_422(self):
        inc = _seed(_repo(), status=IncidentStatus.EN_PROCESO)
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "Nuevo"},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        error_code = resp.json()["detail"]["error_code"]
        assert error_code == "INCIDENT_STATUS_TRANSITION_INVALID"

    def test_from_resuelto_any_returns_422(self):
        inc = _seed(_repo(), status=IncidentStatus.RESUELTO)
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 422
        error_code = resp.json()["detail"]["error_code"]
        assert error_code == "INCIDENT_STATUS_TRANSITION_INVALID"

    def test_unknown_status_returns_422(self):
        inc = _seed(_repo())
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(inc.id),
            json={"status": "Cancelado"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_missing_incident_returns_404(self):
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.patch(
            _URL.format(uuid4()),
            json={"status": "En_proceso"},
            headers=_auth(token),
        )
        assert resp.status_code == 404
        assert resp.json()["detail"]["error_code"] == "INCIDENT_NOT_FOUND"
