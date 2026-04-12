"""Tests del endpoint POST /api/v1/incidents/{id}/technician y TechnicianService."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
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
from app.domain.entities.incident import Incident
from app.domain.entities.user import User
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)
from app.main import app

client = TestClient(app)

ADMIN_ID = uuid4()
TECH_ID = uuid4()
STUDENT_ID = uuid4()
CATEGORY_ID = uuid4()
INCIDENT_ID = uuid4()
ROLE_TECH = uuid4()


def _make_token(user_id: UUID, role_name: str) -> str:
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


class InMemoryTechnicianRepository(TechnicianRepositoryPort):
    """Repositorio en memoria para pruebas de asignación."""

    def __init__(
        self,
        incident_repo: IncidentRepositoryPort,
        assignable_technician_ids: set[UUID],
    ) -> None:
        self._incidents = incident_repo
        self._assignable = assignable_technician_ids

    def find_all(self) -> list[User]:
        return []

    def find_by_id(self, user_id: str) -> User | None:
        return None

    def assign_technician_to_incident(
        self, technician_id: str, incident_id: str
    ) -> User | None:
        inc_uuid = UUID(incident_id)
        tech_uuid = UUID(technician_id)
        incident = self._incidents.get_by_id(inc_uuid)
        if incident is None or tech_uuid not in self._assignable:
            return None
        updated = replace(incident, technician_id=tech_uuid)
        self._incidents.save(updated)
        return User(
            id=tech_uuid,
            first_name="Tech",
            last_name="Test",
            email="tech@test.local",
            password_hash="hashed",
            role_id=ROLE_TECH,
            is_active=True,
            created_at=datetime.now(UTC),
        )

    def technician_available_list_all(self) -> list[User]:
        return []


@pytest.fixture(autouse=True)
def _clean() -> None:
    clear_blacklist()
    reset_technician_dependencies()
    yield
    clear_blacklist()
    app.dependency_overrides.clear()
    reset_technician_dependencies()


def test_technician_service_assign_success() -> None:
    inc_repo = InMemoryIncidentRepository()
    inc_repo.save(
        Incident(
            id=INCIDENT_ID,
            student_id=STUDENT_ID,
            technician_id=None,
            category_id=CATEGORY_ID,
            description="Fuga",
            created_at=datetime.now(UTC),
        )
    )
    tech_repo = InMemoryTechnicianRepository(inc_repo, {TECH_ID})
    service = TechnicianService(tech_repo, inc_repo)
    out = service.assign_technician_to_incident(INCIDENT_ID, TECH_ID)
    assert out.technician_id == TECH_ID


def test_technician_service_incident_not_found() -> None:
    inc_repo = InMemoryIncidentRepository()
    tech_repo = InMemoryTechnicianRepository(inc_repo, {TECH_ID})
    service = TechnicianService(tech_repo, inc_repo)
    with pytest.raises(HTTPException) as exc:
        service.assign_technician_to_incident(uuid4(), TECH_ID)
    assert exc.value.status_code == 404
    assert exc.value.detail["error_code"] == "INCIDENT_NOT_FOUND"


def test_technician_service_technician_not_assignable() -> None:
    inc_repo = InMemoryIncidentRepository()
    inc_repo.save(
        Incident(
            id=INCIDENT_ID,
            student_id=STUDENT_ID,
            technician_id=None,
            category_id=CATEGORY_ID,
            description="Fuga",
            created_at=datetime.now(UTC),
        )
    )
    tech_repo = InMemoryTechnicianRepository(inc_repo, set())
    service = TechnicianService(tech_repo, inc_repo)
    with pytest.raises(HTTPException) as exc:
        service.assign_technician_to_incident(INCIDENT_ID, TECH_ID)
    assert exc.value.status_code == 404
    assert exc.value.detail["error_code"] == "TECHNICIAN_NOT_ASSIGNABLE"


def test_api_assign_technician_success() -> None:
    inc_repo = InMemoryIncidentRepository()
    inc_repo.save(
        Incident(
            id=INCIDENT_ID,
            student_id=STUDENT_ID,
            technician_id=None,
            category_id=CATEGORY_ID,
            description="Fuga",
            created_at=datetime.now(UTC),
        )
    )
    tech_repo = InMemoryTechnicianRepository(inc_repo, {TECH_ID})

    def _override() -> TechnicianService:
        return TechnicianService(tech_repo, inc_repo)

    app.dependency_overrides[get_technician_service] = _override

    token = _make_token(ADMIN_ID, "Administrator")
    response = client.post(
        f"/api/v1/incidents/{INCIDENT_ID}/technician",
        json={"technician_id": str(TECH_ID)},
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["technician_id"] == str(TECH_ID)


def test_api_assign_forbidden_for_student() -> None:
    inc_repo = InMemoryIncidentRepository()
    tech_repo = InMemoryTechnicianRepository(inc_repo, {TECH_ID})

    def _override() -> TechnicianService:
        return TechnicianService(tech_repo, inc_repo)

    app.dependency_overrides[get_technician_service] = _override

    token = _make_token(STUDENT_ID, "Student")
    response = client.post(
        f"/api/v1/incidents/{INCIDENT_ID}/technician",
        json={"technician_id": str(TECH_ID)},
        headers=_auth(token),
    )
    assert response.status_code == 403
