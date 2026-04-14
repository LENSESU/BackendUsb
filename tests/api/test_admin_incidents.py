"""Tests del endpoint GET /api/v1/incidents/admin-inbox.

Valida:
- Solo el rol Administrator puede acceder (Student y Technician reciben 403).
- Sin token -> 401; token invalido -> 401.
- La respuesta sigue la estructura paginada {page, limit, total, total_pages, items}.
- Los items exponen exactamente los campos de la bandeja del administrador.
- Los incidentes llegan ordenados del mas reciente al mas antiguo (orden del repo).
- Los parametros de paginacion funcionan correctamente.
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

ITEM_FIELDS = {
    "id",
    "category_id",
    "technician_id",
    "status",
    "priority",
    "created_at",
    "location",
    "reported_by",
    "reporter_email",
}

PAGINATED_FIELDS = {"page", "limit", "total", "total_pages", "items"}


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


def _seed_incident(repo, student_id=None, created_at=None, technician_id=None):
    """Guarda un incidente minimo en el repositorio in-memory."""
    from app.domain.entities.incident import Incident

    incident = Incident(
        id=uuid4(),
        student_id=student_id or STUDENT_ID,
        technician_id=technician_id,
        category_id=CATEGORY_ID,
        description="Luminaria danada en el pasillo B",
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


# ── Estructura de la respuesta paginada ──────────────────────────────────────


class TestAdminInboxPaginatedShape:
    def test_response_has_pagination_envelope(self):
        """La respuesta tiene el mismo envoltorio que list_incidents."""
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert set(resp.json().keys()) == PAGINATED_FIELDS

    def test_empty_repo_returns_zero_total(self):
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["total_pages"] == 0

    def test_default_pagination_params(self):
        """Sin query params, page=1 y limit=10."""
        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        body = resp.json()
        assert body["page"] == 1
        assert body["limit"] == 10

    def test_total_reflects_incident_count(self):
        import app.api.routes.incidents as incidents_mod

        for _ in range(3):
            _seed_incident(incidents_mod._repository)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.json()["total"] == 3

    def test_pagination_slices_correctly(self):
        """page=2&limit=2 con 3 incidentes devuelve 1 item."""
        import app.api.routes.incidents as incidents_mod

        for _ in range(3):
            _seed_incident(incidents_mod._repository)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get(
            "/api/v1/incidents/admin-inbox?page=2&limit=2",
            headers=_auth(token),
        )
        body = resp.json()
        assert body["page"] == 2
        assert body["limit"] == 2
        assert body["total_pages"] == 2
        assert len(body["items"]) == 1


# ── Campos de cada item ───────────────────────────────────────────────────────


class TestAdminInboxItemFields:
    def test_item_fields(self):
        """Cada item expone exactamente los campos de la bandeja."""
        import app.api.routes.incidents as incidents_mod

        _seed_incident(incidents_mod._repository)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert set(resp.json()["items"][0].keys()) == ITEM_FIELDS

    def test_reported_by_matches_student(self):
        """reported_by coincide con el usuario que reporto el incidente."""
        import app.api.routes.incidents as incidents_mod

        expected_student = uuid4()
        _seed_incident(incidents_mod._repository, student_id=expected_student)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.json()["items"][0]["reported_by"] == str(expected_student)

    def test_item_includes_assigned_technician(self):
        """La bandeja admin refleja el técnico asignado cuando existe."""
        import app.api.routes.incidents as incidents_mod

        expected_tech = uuid4()
        _seed_incident(incidents_mod._repository, technician_id=expected_tech)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        assert resp.json()["items"][0]["technician_id"] == str(expected_tech)

    def test_reporter_email_field_is_present(self):
        """reporter_email existe en cada item (None en repo in-memory sin usuarios)."""
        import app.api.routes.incidents as incidents_mod

        _seed_incident(incidents_mod._repository)

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        item = resp.json()["items"][0]
        assert "reporter_email" in item

    def test_ordered_most_recent_first(self):
        """Los items llegan del mas reciente al mas antiguo (orden del repositorio)."""
        import app.api.routes.incidents as incidents_mod

        repo = incidents_mod._repository
        _seed_incident(repo, created_at=datetime(2026, 4, 9, tzinfo=UTC))
        _seed_incident(repo, created_at=datetime(2026, 4, 11, tzinfo=UTC))
        _seed_incident(repo, created_at=datetime(2026, 4, 10, tzinfo=UTC))

        token = _make_token(ADMIN_ID, "Administrator")
        resp = client.get("/api/v1/incidents/admin-inbox", headers=_auth(token))
        dates = [item["created_at"] for item in resp.json()["items"]]
        assert dates == sorted(dates, reverse=True)
