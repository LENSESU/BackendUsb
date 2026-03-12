"""Tests para protección de endpoints de Items (#61, #63).

Archivo NUEVO creado para validar los cambios de las issues:

- **#61 – Proteger endpoints del backend:**
  Clase ``TestEndpointsRequireAuth`` (6 tests):
    * Sin token → 403 para GET list, GET by id, POST, DELETE.
    * Token inválido → 401.
    * Token revocado (blacklisted) → 401.

  Clase ``TestAuthenticatedAccess`` (6 tests):
    * Token válido de Student puede listar, crear y obtener items.
    * Token de Administrator puede listar.
    * Token de Technician puede crear.
    * Item inexistente → 404.

- **#63 – Validar accesos cruzados:**
  Clase ``TestCrossAccessValidation`` (6 tests):
    * El dueño puede eliminar su propio item (204).
    * Un Student que NO es dueño recibe 403 CROSS_ACCESS_DENIED.
    * Un Technician que NO es dueño recibe 403 CROSS_ACCESS_DENIED.
    * Un Administrator puede eliminar cualquier item (204, bypass).
    * Item inexistente → 404.
    * ``owner_id`` se asigna correctamente al crear.

Total: 18 tests.  No requieren base de datos (JWT se genera en memoria,
items usan ``InMemoryItemRepository``, ``role_name`` está en el token).
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.main import app

client = TestClient(app)

# ── Helpers ──────────────────────────────────────────────────────────────────

ADMIN_USER_ID = uuid4()
STUDENT_USER_ID = uuid4()
STUDENT2_USER_ID = uuid4()
TECH_USER_ID = uuid4()


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


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean():
    """Limpia blacklist y repositorio in-memory entre tests."""
    clear_blacklist()
    import app.api.routes.items as items_mod

    items_mod._repository = None
    yield
    clear_blacklist()
    items_mod._repository = None


# ── #61  Endpoints protegidos ────────────────────────────────────────────────


class TestEndpointsRequireAuth:
    """Todos los endpoints de /items deben rechazar peticiones sin token."""

    def test_list_items_no_token_returns_403(self):
        r = client.get("/api/v1/items/")
        assert r.status_code == 403

    def test_get_item_no_token_returns_403(self):
        r = client.get(f"/api/v1/items/{uuid4()}")
        assert r.status_code == 403

    def test_create_item_no_token_returns_403(self):
        r = client.post("/api/v1/items/", json={"name": "test"})
        assert r.status_code == 403

    def test_delete_item_no_token_returns_403(self):
        r = client.delete(f"/api/v1/items/{uuid4()}")
        assert r.status_code == 403

    def test_invalid_token_returns_401(self):
        headers = _auth("not.a.valid.jwt")
        r = client.get("/api/v1/items/", headers=headers)
        assert r.status_code == 401

    def test_revoked_token_returns_401(self):
        token = _make_token(STUDENT_USER_ID, "Student")
        from app.core.token_blacklist import add_token_to_blacklist

        add_token_to_blacklist(token)
        r = client.get("/api/v1/items/", headers=_auth(token))
        assert r.status_code == 401


# ── #61  Acceso autenticado funciona ─────────────────────────────────────────


class TestAuthenticatedAccess:
    """Endpoints permiten acceso con token válido y rol correcto."""

    def test_list_items_returns_200(self):
        token = _make_token(STUDENT_USER_ID, "Student")
        r = client.get("/api/v1/items/", headers=_auth(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_item_returns_201(self):
        token = _make_token(STUDENT_USER_ID, "Student")
        r = client.post(
            "/api/v1/items/",
            json={"name": "Mi item", "description": "desc"},
            headers=_auth(token),
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Mi item"
        assert data["owner_id"] == str(STUDENT_USER_ID)

    def test_get_item_returns_200(self):
        token = _make_token(STUDENT_USER_ID, "Student")
        # Crear primero
        r = client.post(
            "/api/v1/items/",
            json={"name": "read-me"},
            headers=_auth(token),
        )
        item_id = r.json()["id"]

        r2 = client.get(f"/api/v1/items/{item_id}", headers=_auth(token))
        assert r2.status_code == 200
        assert r2.json()["name"] == "read-me"

    def test_get_nonexistent_item_returns_404(self):
        token = _make_token(STUDENT_USER_ID, "Student")
        r = client.get(f"/api/v1/items/{uuid4()}", headers=_auth(token))
        assert r.status_code == 404

    def test_admin_can_list_items(self):
        token = _make_token(ADMIN_USER_ID, "Administrator")
        r = client.get("/api/v1/items/", headers=_auth(token))
        assert r.status_code == 200

    def test_technician_can_create_items(self):
        token = _make_token(TECH_USER_ID, "Technician")
        r = client.post(
            "/api/v1/items/",
            json={"name": "Tech item"},
            headers=_auth(token),
        )
        assert r.status_code == 201


# ── #63  Validación de acceso cruzado ────────────────────────────────────────


class TestCrossAccessValidation:
    """
    Un usuario no-admin NO puede eliminar items de otro usuario.
    Un Administrator SÍ puede eliminar cualquier item.
    El dueño SÍ puede eliminar su propio item.
    """

    def _create_item_as(self, user_id, role_name: str) -> dict:
        token = _make_token(user_id, role_name)
        r = client.post(
            "/api/v1/items/",
            json={"name": f"item-{user_id}"},
            headers=_auth(token),
        )
        assert r.status_code == 201
        return r.json()

    def test_owner_can_delete_own_item(self):
        item = self._create_item_as(STUDENT_USER_ID, "Student")
        token = _make_token(STUDENT_USER_ID, "Student")
        r = client.delete(f"/api/v1/items/{item['id']}", headers=_auth(token))
        assert r.status_code == 204

    def test_non_owner_student_cannot_delete(self):
        item = self._create_item_as(STUDENT_USER_ID, "Student")
        other_token = _make_token(STUDENT2_USER_ID, "Student")
        r = client.delete(f"/api/v1/items/{item['id']}", headers=_auth(other_token))
        assert r.status_code == 403
        assert r.json()["detail"]["error_code"] == "CROSS_ACCESS_DENIED"

    def test_non_owner_technician_cannot_delete(self):
        item = self._create_item_as(STUDENT_USER_ID, "Student")
        tech_token = _make_token(TECH_USER_ID, "Technician")
        r = client.delete(f"/api/v1/items/{item['id']}", headers=_auth(tech_token))
        assert r.status_code == 403
        assert r.json()["detail"]["error_code"] == "CROSS_ACCESS_DENIED"

    def test_admin_can_delete_any_item(self):
        item = self._create_item_as(STUDENT_USER_ID, "Student")
        admin_token = _make_token(ADMIN_USER_ID, "Administrator")
        r = client.delete(f"/api/v1/items/{item['id']}", headers=_auth(admin_token))
        assert r.status_code == 204

    def test_delete_nonexistent_item_returns_404(self):
        token = _make_token(ADMIN_USER_ID, "Administrator")
        r = client.delete(f"/api/v1/items/{uuid4()}", headers=_auth(token))
        assert r.status_code == 404

    def test_owner_id_is_set_on_creation(self):
        """Verifica que al crear un item, el owner_id se asigna correctamente."""
        item = self._create_item_as(STUDENT_USER_ID, "Student")
        assert item["owner_id"] == str(STUDENT_USER_ID)
