"""Tests del endpoint GET /api/v1/incidents/admin-inbox.

Valida:
- Solo el rol Administrator puede acceder (Student y Technician reciben 403).
- Sin token -> 401; token inválido -> 401.
- La respuesta es una lista con los campos correctos de la bandeja.
- Los incidentes llegan ordenados del más reciente al más antiguo.
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)
from app.main import app

client = TestClient(app)

ADMIN_ID = uuid4()
STUDENT_ID = uuid4()
TECH_ID = uuid4()
CATEGORY_ID = uuid4()

EXPECTED_FIELDS = {
    "id",
    "category_id",
    "status",
    "priority",
    "created_at",
    "location",
    "reported_by",
}


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


def _seed_incident(repo, student_id=None, created_at=None):
    """Guarda un incidente mínimo en el repositorio in-memory."""
    from app.domain.entities.incident import Incident

    incident = Incident(
        id=uuid4(),
        student_id=student_id or STUDENT_ID,
        technician_id=None,
        category_id=CATEGORY_ID,
        description="Luminaria dañada en el pasillo B",
        created_at=created_at or datetime.now(UTC),
    )
    repo.save(incident)
    return incident


@pytest.fixture(autouse=True)
def _clean():
    """Inyecta un repositorio in-memory limpio y reinicia la blacklist entre tests."""
    import app.api.routes.incidents as incidents_mod

    incidents_mod._repository = InMemoryIncidentRepository()
    clear_blacklist()
    yield
    incidents_mod._repository = None
    clear_blacklist()


# ── Acceso por rol ────────────────────────────────────────────────────────────


class TestAdminInboxAccess:
    def test_administrator_gets_200(self):
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.status_code == 200

    def test_student_gets_403(self):
        token = _make_token(STUDENT_ID, "Student")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.status_code == 403

    def test_technician_gets_403(self):
        token = _make_token(TECH_ID, "Technician")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.status_code == 403

    def test_no_token_gets_401(self):
        resp = client.get("/api/v1/incidents/admin-inbox")
        assert resp.status_code == 401

    def test_invalid_token_gets_401(self):
        resp = client.get(
            "/api/v1/incidents/admin-inbox",
            headers=_auth("esto.no.es.un.jwt"),
        )
        assert resp.status_code == 401


# ── Forma de la respuesta ─────────────────────────────────────────────────────


class TestAdminInboxResponse:
    def test_returns_list(self):
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert isinstance(resp.json(), list)

    def test_empty_list_when_no_incidents(self):
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.json() == []

    def test_response_fields(self):
        """Cada elemento expone exactamente los campos de la bandeja."""
        import app.api.routes.incidents as incidents_mod

        _seed_incident(incidents_mod._repository)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert set(resp.json()[0].keys()) == EXPECTED_FIELDS

    def test_reported_by_matches_student(self):
        """reported_by coincide con el usuario que reportó el incidente."""
        import app.api.routes.incidents as incidents_mod

        expected_student = uuid4()
        _seed_incident(incidents_mod._repository, student_id=expected_student)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.json()[0]["reported_by"] == str(expected_student)

    def test_ordered_most_recent_first(self):
        """Los incidentes se retornan del más reciente al más antiguo."""
        import app.api.routes.incidents as incidents_mod

        repo = incidents_mod._repository
        _seed_incident(repo, created_at=datetime(2026, 4, 9, tzinfo=UTC))
        _seed_incident(repo, created_at=datetime(2026, 4, 11, tzinfo=UTC))
        _seed_incident(repo, created_at=datetime(2026, 4, 10, tzinfo=UTC))

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        dates = [item["created_at"] for item in resp.json()]
        assert dates == sorted(dates, reverse=True)
