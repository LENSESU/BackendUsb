"""Tests para endpoints de categorías de incidentes."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.incident_category import get_incident_category_service
from app.application.services.incident_category_service import IncidentCategoryService
from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.infrastructure.adapters.incident_category_repository_in_memory import (
    InMemoryIncidentCategoryRepository,
)
from app.main import app

client = TestClient(app)

# ── Helpers ────────────────────────────────────────────────────────────────

ADMIN_ID = uuid4()
STUDENT_ID = uuid4()
TECH_ID = uuid4()


def _make_token(user_id, role_name: str) -> str:
    return create_access_token(
        data={
            "sub": str(user_id),
            "email": f"{role_name.lower()}@usb.ve",
            "role_id": str(uuid4()),
            "role_name": role_name,
        }
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _override_repo():
    """Sustituye el repositorio SQL por uno en memoria para tests aislados."""
    repo = InMemoryIncidentCategoryRepository()
    service = IncidentCategoryService(repository=repo)
    app.dependency_overrides[get_incident_category_service] = lambda: service
    clear_blacklist()
    yield
    app.dependency_overrides.pop(get_incident_category_service, None)
    clear_blacklist()


# ── Control de acceso ─────────────────────────────────────────────────────


class TestAccessControl:
    """Solo Administrador puede crear; cualquier rol autenticado puede listar."""

    def test_create_without_token_returns_403(self):
        r = client.post("/api/v1/categories/", json={"name": "Hardware"})
        assert r.status_code == 403

    def test_create_as_student_returns_403(self):
        r = client.post(
            "/api/v1/categories/",
            json={"name": "Hardware"},
            headers=_auth(_make_token(STUDENT_ID, "Student")),
        )
        assert r.status_code == 403

    def test_create_as_technician_returns_403(self):
        r = client.post(
            "/api/v1/categories/",
            json={"name": "Hardware"},
            headers=_auth(_make_token(TECH_ID, "Technician")),
        )
        assert r.status_code == 403

    def test_list_without_token_returns_403(self):
        r = client.get("/api/v1/categories/")
        assert r.status_code == 403

    def test_list_as_student_returns_200(self):
        r = client.get(
            "/api/v1/categories/",
            headers=_auth(_make_token(STUDENT_ID, "Student")),
        )
        assert r.status_code == 200

    def test_list_as_technician_returns_200(self):
        r = client.get(
            "/api/v1/categories/",
            headers=_auth(_make_token(TECH_ID, "Technician")),
        )
        assert r.status_code == 200


# ── Creación de categorías ────────────────────────────────────────────────


class TestCreateCategory:
    """Valida creación correcta y unicidad de nombre."""

    def test_admin_creates_category_returns_201(self):
        r = client.post(
            "/api/v1/categories/",
            json={"name": "Hardware", "description": "Problemas de hardware"},
            headers=_auth(_make_token(ADMIN_ID, "Administrator")),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Hardware"
        assert data["description"] == "Problemas de hardware"
        assert "id" in data

    def test_category_without_description_is_accepted(self):
        r = client.post(
            "/api/v1/categories/",
            json={"name": "Redes"},
            headers=_auth(_make_token(ADMIN_ID, "Administrator")),
        )
        assert r.status_code == 201
        assert r.json()["description"] is None

    def test_duplicate_name_returns_409(self):
        token = _make_token(ADMIN_ID, "Administrator")
        client.post(
            "/api/v1/categories/",
            json={"name": "Software"},
            headers=_auth(token),
        )
        r = client.post(
            "/api/v1/categories/",
            json={"name": "Software"},
            headers=_auth(token),
        )
        assert r.status_code == 409

    def test_duplicate_name_case_insensitive_returns_409(self):
        token = _make_token(ADMIN_ID, "Administrator")
        client.post(
            "/api/v1/categories/",
            json={"name": "Red"},
            headers=_auth(token),
        )
        r = client.post(
            "/api/v1/categories/",
            json={"name": "RED"},
            headers=_auth(token),
        )
        assert r.status_code == 409

    def test_created_category_appears_in_list(self):
        admin_token = _make_token(ADMIN_ID, "Administrator")
        student_token = _make_token(STUDENT_ID, "Student")
        client.post(
            "/api/v1/categories/",
            json={"name": "Electricidad"},
            headers=_auth(admin_token),
        )
        r = client.get("/api/v1/categories/", headers=_auth(student_token))
        assert r.status_code == 200
        items = r.json()["items"]
        assert any(c["name"] == "Electricidad" for c in items)

    def test_list_response_has_count(self):
        token = _make_token(ADMIN_ID, "Administrator")
        client.post("/api/v1/categories/", json={"name": "A"}, headers=_auth(token))
        client.post("/api/v1/categories/", json={"name": "B"}, headers=_auth(token))
        r = client.get("/api/v1/categories/", headers=_auth(token))
        assert r.json()["count"] == 2
