"""Tests del endpoint consolidado de dashboard."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.suggestion import get_suggestion_service
from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.application.services.suggestion_service import SuggestionService
from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.domain.entities.incident import Incident
from app.domain.entities.suggestion import Suggestion
from app.infrastructure.adapters.in_memory_incident_repository import (
    InMemoryIncidentRepository,
)
from app.main import app

client = TestClient(app)

STUDENT_USER_ID = uuid4()
OTHER_USER_ID = uuid4()


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


class InMemorySuggestionRepository(SuggestionRepositoryPort):
    def __init__(self) -> None:
        self._by_id: dict[UUID, Suggestion] = {}

    def get_by_id(self, suggestion_id: UUID) -> Suggestion | None:
        return self._by_id.get(suggestion_id)

    def list_all(self) -> list[Suggestion]:
        return list(self._by_id.values())

    def list_popular(self, limit: int) -> list[Suggestion]:
        ordered = sorted(
            self._by_id.values(),
            key=lambda s: (s.total_votes, s.created_at or datetime.min.replace(tzinfo=UTC)),
            reverse=True,
        )
        return ordered[:limit]

    def save(self, suggestion: Suggestion) -> Suggestion:
        self._by_id[suggestion.id] = suggestion
        return suggestion

    def delete(self, suggestion_id: UUID) -> bool:
        return self._by_id.pop(suggestion_id, None) is not None


@pytest.fixture(autouse=True)
def _clean() -> None:
    clear_blacklist()
    suggestion_repo = InMemorySuggestionRepository()
    incident_repo = InMemoryIncidentRepository()

    def _override_suggestion_service() -> SuggestionService:
        return SuggestionService(repository=suggestion_repo)

    app.dependency_overrides[get_suggestion_service] = _override_suggestion_service

    import app.api.routes.incidents as incidents_mod

    incidents_mod._repository = incident_repo

    now = datetime.now(UTC)
    # 6 incidentes del usuario actual (el dashboard debe devolver solo 5)
    for idx in range(6):
        incident_repo.save(
            Incident(
                id=uuid4(),
                student_id=STUDENT_USER_ID,
                technician_id=None,
                category_id=uuid4(),
                description=f"Incidente {idx}",
                status="Nuevo",
                priority=None,
                before_photo_id=None,
                after_photo_id=None,
                created_at=now - timedelta(minutes=idx),
                updated_at=None,
                location=None,
            )
        )
    # Incidente de otro usuario (no debe aparecer)
    incident_repo.save(
        Incident(
            id=uuid4(),
            student_id=OTHER_USER_ID,
            technician_id=None,
            category_id=uuid4(),
            description="Incidente otro usuario",
            status="Nuevo",
            priority=None,
            before_photo_id=None,
            after_photo_id=None,
            created_at=now,
            updated_at=None,
            location=None,
        )
    )

    # 6 sugerencias (el dashboard debe devolver top 5 por votos)
    for idx, votes in enumerate((2, 10, 5, 1, 8, 3)):
        suggestion_repo.save(
            Suggestion(
                id=uuid4(),
                student_id=STUDENT_USER_ID,
                title=f"Sugerencia {idx}",
                content="Contenido",
                total_votes=votes,
                created_at=now - timedelta(minutes=idx),
            )
        )

    yield

    app.dependency_overrides.pop(get_suggestion_service, None)
    incidents_mod._repository = None
    clear_blacklist()


def test_dashboard_returns_user_incidents_and_top_suggestions() -> None:
    token = _make_token(STUDENT_USER_ID, "Student")
    response = client.get("/api/v1/dashboard/", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()

    assert body["user"]["user_id"] == str(STUDENT_USER_ID)
    assert len(body["recentIncidents"]) == 5
    assert all(i["description"].startswith("Incidente") for i in body["recentIncidents"])
    assert "categoria" in body["recentIncidents"][0]

    assert len(body["suggestions"]) == 5
    assert body["suggestions"][0]["total_votos"] == 10


def test_dashboard_requires_authentication() -> None:
    response = client.get("/api/v1/dashboard/")
    assert response.status_code == 401
