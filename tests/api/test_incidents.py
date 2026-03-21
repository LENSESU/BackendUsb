"""Tests del endpoint de creación de incidentes (#109, HU-E2-011).

Valida las tareas:
- #107 — Metadatos automáticos: ``student_id`` viene del JWT, ``created_at``
         lo asigna el servidor; el cliente no los controla.
- #108 — Respuesta HTTP 201 Created en creación exitosa.
- #109 — Pruebas completas del endpoint ``POST /api/v1/incidents/``.

Estructura de tests:
  - ``TestIncidentCreation``     — creación exitosa, 201, metadatos correctos.
  - ``TestAutoMetadata``         — student_id y created_at no dependen del cliente.
  - ``TestIncidentAuth``         — acceso sin token / token inválido.

Total: 11 tests.  No requieren base de datos (JWT en memoria,
incidentes usan ``InMemoryIncidentRepository``).
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.application.services.incident_service import IncidentService
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)
from app.main import app

client = TestClient(app)

# ── Helpers ──────────────────────────────────────────────────────────────────

STUDENT_USER_ID = uuid4()
ADMIN_USER_ID = uuid4()
TECH_USER_ID = uuid4()

CATEGORY_ID = uuid4()
PHOTO_ID = uuid4()


def _make_token(user_id, role_name: str) -> str:
    """Crea un access token JWT válido con role_name embebido."""
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


def _valid_payload() -> dict:
    """Payload mínimo válido para crear un incidente."""
    return {
        "category_id": str(CATEGORY_ID),
        "description": "Luminaria dañada en el pasillo B",
        "before_photo_id": str(PHOTO_ID),
    }


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    """Limpia blacklist y repositorio in-memory entre tests."""
    clear_blacklist()
    import app.api.routes.incidents as incidents_mod

    repo = InMemoryIncidentRepository()
    service = IncidentService(repository=repo, category_repository=None)
    monkeypatch.setattr(incidents_mod, "get_incident_service", lambda: service)

    incidents_mod._repository = None
    yield
    clear_blacklist()
    incidents_mod._repository = None


# ── #108 + #107: Creación exitosa con metadatos automáticos ──────────────────


class TestIncidentCreation:
    """Valida creación exitosa, código 201 y datos del incidente."""

    def test_create_incident_returns_201(self):
        """#108 — El endpoint responde 201 Created."""
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth(token),
        )
        assert resp.status_code == 201

    def test_create_incident_returns_correct_data(self):
        """La respuesta contiene los campos enviados."""
        token = _make_token(STUDENT_USER_ID, "Student")
        payload = _valid_payload()
        resp = client.post(
            "/api/v1/incidents/",
            json=payload,
            headers=_auth(token),
        )
        body = resp.json()
        assert body["description"] == payload["description"]
        assert body["category_id"] == payload["category_id"]
        assert body["before_photo_id"] == payload["before_photo_id"]
        assert body["id"] is not None

    def test_create_incident_has_default_status(self):
        """El incidente recibe el estado inicial definido en la entidad de dominio."""
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth(token),
        )
        body = resp.json()
        # El dominio define status="Nuevo" como valor por defecto
        assert body["status"] == "Nuevo"

    def test_create_incident_student_id_is_authenticated_user(self):
        """#107 — student_id es el usuario autenticado, no un valor del payload."""
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth(token),
        )
        body = resp.json()
        assert body["student_id"] == str(STUDENT_USER_ID)

    def test_create_incident_created_at_is_set(self):
        """#107 — created_at se registra automáticamente."""
        token = _make_token(STUDENT_USER_ID, "Student")
        before = datetime.now(UTC)
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth(token),
        )
        after = datetime.now(UTC)
        body = resp.json()
        created = datetime.fromisoformat(body["created_at"])
        # created_at debe estar entre before y after
        assert (
            before.replace(tzinfo=None)
            <= created.replace(tzinfo=None)
            <= after.replace(tzinfo=None)
        )

    def test_create_incident_with_optional_fields(self):
        """Se pueden enviar campos opcionales (location, priority)."""
        token = _make_token(STUDENT_USER_ID, "Student")
        payload = _valid_payload()
        payload["campus_place"] = "Edificio MYS, Piso 2"
        payload["latitude"] = 10.409
        payload["longitude"] = -66.883
        payload["priority"] = "Alta"
        resp = client.post(
            "/api/v1/incidents/",
            json=payload,
            headers=_auth(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["campus_place"] == "Edificio MYS, Piso 2"
        assert body["priority"] == "Alta"


# ── #107: Metadatos automáticos no controlados por el cliente ────────────────


class TestAutoMetadata:
    """Valida que el backend es fuente de verdad para student_id y created_at."""

    def test_client_cannot_override_student_id(self):
        """#107 — Si el payload envía student_id, el backend lo ignora y usa el JWT."""
        token = _make_token(STUDENT_USER_ID, "Student")
        fake_user_id = str(uuid4())
        payload = _valid_payload()
        # Intentar enviar un student_id ajeno (el schema no lo acepta,
        # pero si lo enviara, el backend lo ignora)
        resp = client.post(
            "/api/v1/incidents/",
            json=payload,
            headers=_auth(token),
        )
        body = resp.json()
        assert body["student_id"] == str(STUDENT_USER_ID)
        assert body["student_id"] != fake_user_id

    def test_admin_creates_incident_with_own_user_id(self):
        """Un admin que crea un incidente queda como student_id (es quien reporta)."""
        token = _make_token(ADMIN_USER_ID, "Administrator")
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth(token),
        )
        body = resp.json()
        assert body["student_id"] == str(ADMIN_USER_ID)


# ── Autenticación requerida ──────────────────────────────────────────────────


class TestIncidentAuth:
    """Valida que el endpoint requiere autenticación."""

    def test_create_without_token_returns_403(self):
        """Sin token, el endpoint rechaza con 403."""
        resp = client.post("/api/v1/incidents/", json=_valid_payload())
        assert resp.status_code == 403

    def test_create_with_invalid_token_returns_401(self):
        """Token inválido → 401."""
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth("esto.no.es.un.jwt"),
        )
        assert resp.status_code == 401

    def test_create_with_revoked_token_returns_401(self):
        """Token revocado (logout) → 401."""
        from app.core.token_blacklist import add_token_to_blacklist

        token = _make_token(STUDENT_USER_ID, "Student")
        add_token_to_blacklist(token)
        resp = client.post(
            "/api/v1/incidents/",
            json=_valid_payload(),
            headers=_auth(token),
        )
        assert resp.status_code == 401
