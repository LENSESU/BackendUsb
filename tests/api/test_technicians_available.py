"""Tests del endpoint GET /api/v1/technicians/available."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.technician import (
    get_technician_service,
    reset_technician_dependencies,
)
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.ports.technician_repository import TechnicianRepositoryPort
from app.application.services.technician_service import TechnicianService
from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.domain.entities.user import User
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)
from app.main import app

client = TestClient(app)

USER_ID = uuid4()
TECH_A = uuid4()
ROLE_ID = uuid4()


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


class InMemoryTechnicianRepositoryListOnly(TechnicianRepositoryPort):
    """Repositorio en memoria que solo implementa listado disponible."""

    def __init__(self, available: list[User]) -> None:
        self._available = available

    def find_all(self) -> list[User]:
        return []

    def find_by_id(self, user_id: str) -> User | None:
        return None

    def assign_technician_to_incident(
        self, technician_id: str, incident_id: str
    ) -> User | None:
        return None

    def technician_available_list_all(self) -> list[User]:
        return list(self._available)


@pytest.fixture(autouse=True)
def _clean() -> None:
    clear_blacklist()
    reset_technician_dependencies()
    yield
    clear_blacklist()
    app.dependency_overrides.clear()
    reset_technician_dependencies()


def test_list_available_technicians_success() -> None:
    now = datetime.now(UTC)
    tech_user = User(
        id=TECH_A,
        first_name="Ana",
        last_name="Técnico",
        email="ana.tech@example.com",
        password_hash="x",
        role_id=ROLE_ID,
        is_active=True,
        created_at=now,
    )
    inc_repo = InMemoryIncidentRepository()
    repo = InMemoryTechnicianRepositoryListOnly([tech_user])

    def _override() -> TechnicianService:
        return TechnicianService(repo, inc_repo)

    app.dependency_overrides[get_technician_service] = _override

    token = _make_token(USER_ID, "Administrator")
    response = client.get(
        "/api/v1/technicians/available",
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(TECH_A)
    assert body[0]["first_name"] == "Ana"
    assert body[0]["email"] == "ana.tech@example.com"


def test_list_available_technicians_empty_list() -> None:
    inc_repo = InMemoryIncidentRepository()
    repo = InMemoryTechnicianRepositoryListOnly([])

    def _override() -> TechnicianService:
        return TechnicianService(repo, inc_repo)

    app.dependency_overrides[get_technician_service] = _override

    token = _make_token(USER_ID, "Student")
    response = client.get(
        "/api/v1/technicians/available",
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json() == []


def test_list_available_without_token_returns_401() -> None:
    response = client.get("/api/v1/technicians/available")
    assert response.status_code == 401
