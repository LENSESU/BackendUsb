"""Tests del CRUD de sugerencias."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.suggestion import get_suggestion_service
from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.application.services.suggestion_service import SuggestionService
from app.core.security import create_access_token
from app.core.token_blacklist import clear_blacklist
from app.domain.entities.suggestion import Suggestion
from app.main import app

client = TestClient(app)

STUDENT_USER_ID = uuid4()


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
        if suggestion.id is None:
            msg = "La sugerencia debe tener id antes de guardar"
            raise ValueError(msg)
        now = datetime.now(UTC)
        created_at = suggestion.created_at or now
        stored = Suggestion(
            id=suggestion.id,
            student_id=suggestion.student_id,
            title=suggestion.title,
            content=suggestion.content,
            photo_id=suggestion.photo_id,
            total_votes=suggestion.total_votes,
            institutional_comment=suggestion.institutional_comment,
            created_at=created_at,
        )
        self._by_id[stored.id] = stored
        return stored

    def delete(self, suggestion_id: UUID) -> bool:
        if suggestion_id not in self._by_id:
            return False
        del self._by_id[suggestion_id]
        return True


@pytest.fixture(autouse=True)
def _clean():
    clear_blacklist()
    repo = InMemorySuggestionRepository()

    def _override() -> SuggestionService:
        return SuggestionService(repository=repo)

    app.dependency_overrides[get_suggestion_service] = _override
    yield
    app.dependency_overrides.pop(get_suggestion_service, None)
    clear_blacklist()


def _valid_create_payload() -> dict:
    return {
        "estudiante_id": str(STUDENT_USER_ID),
        "titulo": "Mejorar iluminación",
        "contenido": "Detalle de la sugerencia para el campus.",
    }


class TestSuggestionCrud:
    def test_create_returns_201_and_default_votes(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.post(
            "/api/v1/suggestions/",
            json=_valid_create_payload(),
            headers=_auth(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["titulo"] == "Mejorar iluminación"
        assert body["total_votos"] == 0
        assert body["estudiante_id"] == str(STUDENT_USER_ID)
        assert body["id"] is not None

    def test_create_with_total_votos(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        p = _valid_create_payload()
        p["total_votos"] = 5
        resp = client.post(
            "/api/v1/suggestions/",
            json=p,
            headers=_auth(token),
        )
        assert resp.status_code == 201
        assert resp.json()["total_votos"] == 5

    def test_title_too_long_returns_400(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        p = _valid_create_payload()
        p["titulo"] = "x" * 201
        resp = client.post(
            "/api/v1/suggestions/",
            json=p,
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_negative_total_votos_returns_400(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        p = _valid_create_payload()
        p["total_votos"] = -1
        resp = client.post(
            "/api/v1/suggestions/",
            json=p,
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_empty_title_content_returns_400(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        p = _valid_create_payload()
        p["titulo"] = "   "
        resp = client.post(
            "/api/v1/suggestions/",
            json=p,
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_get_by_id_404(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.get(
            f"/api/v1/suggestions/{uuid4()}",
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_list_update_delete(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        create = client.post(
            "/api/v1/suggestions/",
            json=_valid_create_payload(),
            headers=_auth(token),
        )
        assert create.status_code == 201
        sid = create.json()["id"]

        listed = client.get("/api/v1/suggestions/", headers=_auth(token))
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        upd = client.patch(
            f"/api/v1/suggestions/{sid}",
            json={"titulo": "Nuevo título"},
            headers=_auth(token),
        )
        assert upd.status_code == 200
        assert upd.json()["titulo"] == "Nuevo título"

        null_votes = client.patch(
            f"/api/v1/suggestions/{sid}",
            json={"total_votos": None},
            headers=_auth(token),
        )
        assert null_votes.status_code == 400
        body = null_votes.json()
        assert body.get("error_code") == "SUGGESTION_VALIDATION_ERROR"

        deleted = client.delete(
            f"/api/v1/suggestions/{sid}",
            headers=_auth(token),
        )
        assert deleted.status_code == 204

        missing = client.get(
            f"/api/v1/suggestions/{sid}",
            headers=_auth(token),
        )
        assert missing.status_code == 404

    def test_popular_returns_sorted_and_limited(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")

        p1 = _valid_create_payload()
        p1["titulo"] = "A"
        p1["total_votos"] = 2
        p2 = _valid_create_payload()
        p2["titulo"] = "B"
        p2["total_votos"] = 10
        p3 = _valid_create_payload()
        p3["titulo"] = "C"
        p3["total_votos"] = 5

        for payload in (p1, p2, p3):
            resp = client.post(
                "/api/v1/suggestions/",
                json=payload,
                headers=_auth(token),
            )
            assert resp.status_code == 201

        popular = client.get(
            "/api/v1/suggestions/popular?limit=2",
            headers=_auth(token),
        )
        assert popular.status_code == 200
        body = popular.json()
        assert len(body) == 2
        assert body[0]["titulo"] == "B"
        assert body[0]["total_votos"] == 10
        assert body[1]["titulo"] == "C"
        assert body[1]["total_votos"] == 5

    def test_popular_rejects_invalid_limit(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.get(
            "/api/v1/suggestions/popular?limit=0",
            headers=_auth(token),
        )
        assert resp.status_code == 400
