"""Tests del CRUD de sugerencias."""

from datetime import UTC, datetime
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.storage import get_incident_evidence_service
from app.api.dependencies.suggestion import get_suggestion_service
from app.application.ports.file_repository import FileRepositoryPort
from app.application.ports.file_storage import FileStoragePort, StoredFileResult
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.ports.suggestion_repository import SuggestionRepositoryPort
from app.application.services.incident_evidence_service import IncidentEvidenceService
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

    def list_by_student(self, student_id: UUID) -> list[Suggestion]:
        return sorted(
            [s for s in self._by_id.values() if s.student_id == student_id],
            key=lambda s: s.created_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

    def list_popular(self, limit: int) -> list[Suggestion]:
        ordered = sorted(
            self._by_id.values(),
            key=lambda s: (
                s.total_votes,
                s.created_at or datetime.min.replace(tzinfo=UTC),
            ),
            reverse=True,
        )
        return ordered[:limit]

    def list_filtered(
        self,
        order_by: str = "fecha",
        tags: list[str] | None = None,
    ) -> list[Suggestion]:
        result = list(self._by_id.values())
        if tags:
            tag_set = {t.strip().lower() for t in tags if t.strip()}
            result = [
                s
                for s in result
                if s.tags and any(t.lower() in tag_set for t in s.tags)
            ]
        if order_by == "popularidad":
            result.sort(
                key=lambda s: (
                    s.total_votes,
                    s.created_at or datetime.min.replace(tzinfo=UTC),
                ),
                reverse=True,
            )
        else:
            result.sort(
                key=lambda s: s.created_at or datetime.min.replace(tzinfo=UTC),
                reverse=True,
            )
        return result

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
            tags=suggestion.tags or [],
        )
        self._by_id[stored.id] = stored
        return stored

    def save_with_tags(
        self, suggestion: Suggestion, tag_names: list[str] | None = None
    ) -> Suggestion:
        """Guarda sugerencia con etiquetas (mock en memoria)."""
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
            tags=tag_names or [],
        )
        self._by_id[stored.id] = stored
        return stored

    def delete(self, suggestion_id: UUID) -> bool:
        if suggestion_id not in self._by_id:
            return False
        del self._by_id[suggestion_id]
        return True


# Mocks para el servicio de almacenamiento
class MockFileRepository(FileRepositoryPort):
    """Mock del repositorio de archivos."""

    def __init__(self) -> None:
        self._files: dict[UUID, str] = {}

    def create_file(self, *, url: str, file_type: str | None, uploaded_by_user_id: UUID | None) -> UUID:
        file_id = uuid4()
        self._files[file_id] = url  # Almacena la URL directamente
        return file_id

    def get_by_id(self, file_id: UUID) -> str | None:
        return self._files.get(file_id)  # Retorna la URL como string


class MockFileStorage(FileStoragePort):
    """Mock del adaptador de almacenamiento (simula Google Cloud Storage)."""

    async def upload_incident_evidence(
        self,
        *,
        incident_id: UUID,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        return StoredFileResult(
            object_name=f"incidents/{incident_id}/{filename}",
            file_url=f"https://storage.googleapis.com/multimedia_incidents/incidents/{incident_id}/{filename}",
        )

    async def upload_file(
        self,
        *,
        prefix: str,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> StoredFileResult:
        return StoredFileResult(
            object_name=f"{prefix}/{filename}",
            file_url=f"https://storage.googleapis.com/multimedia_incidents/{prefix}/{filename}",
        )


class MockIncidentRepository(IncidentRepositoryPort):
    """Mock del repositorio de incidentes (no es necesario para sugerencias)."""

    def get_by_id(self, incident_id: UUID):
        return None

    def save(self, incident):
        pass

    def delete(self, incident_id: UUID) -> bool:
        return False

    def list_all(self) -> list:
        return []


@pytest.fixture(autouse=True)
def _clean():
    clear_blacklist()
    repo = InMemorySuggestionRepository()
    file_repo = MockFileRepository()
    storage = MockFileStorage()
    incident_repo = MockIncidentRepository()

    def _override_suggestion_service() -> SuggestionService:
        return SuggestionService(repository=repo)

    def _override_evidence_service() -> IncidentEvidenceService:
        return IncidentEvidenceService(
            storage=storage,
            incident_repository=incident_repo,
            file_repository=file_repo,
        )

    app.dependency_overrides[get_suggestion_service] = _override_suggestion_service
    app.dependency_overrides[get_incident_evidence_service] = _override_evidence_service
    yield
    app.dependency_overrides.pop(get_suggestion_service, None)
    app.dependency_overrides.pop(get_incident_evidence_service, None)
    clear_blacklist()


def _valid_create_params() -> dict:
    """Parámetros válidos para crear sugerencia (Form data)."""
    return {
        "titulo": "Mejorar iluminación",
        "contenido": "Detalle de la sugerencia para el campus.",
    }


class TestSuggestionCrud:
    def test_create_without_photo_returns_201(self) -> None:
        """Crea sugerencia sin foto."""
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.post(
            "/api/v1/suggestions/",
            data=_valid_create_params(),
            headers=_auth(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["titulo"] == "Mejorar iluminación"
        assert body["total_votos"] == 0
        assert body["estudiante_id"] == str(STUDENT_USER_ID)
        assert body["id"] is not None
        assert body["foto_url"] is None

    def test_create_with_tags_returns_201(self) -> None:
        """Crea sugerencia con etiquetas separadas por coma."""
        token = _make_token(STUDENT_USER_ID, "Student")
        data = _valid_create_params()
        data["etiquetas"] = "iluminación,infraestructura,urgente"
        resp = client.post(
            "/api/v1/suggestions/",
            data=data,
            headers=_auth(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["etiquetas"] == ["iluminación", "infraestructura", "urgente"]

    def test_create_with_photo_returns_201_and_has_photo_url(self) -> None:
        """Crea sugerencia CON foto. Verifica que foto_url sea una URL válida de Google Cloud Storage."""
        token = _make_token(STUDENT_USER_ID, "Student")
        
        # Crear una imagen JPEG válida en memoria
        jpeg_bytes = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c'
            b'\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
            b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00'
            b'\x01\x00\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
            b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06'
            b'\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03'
            b'\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06'
            b'\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t'
            b'\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz'
            b'\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a'
            b'\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9'
            b'\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8'
            b'\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5'
            b'\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd3\xff'
            b'\xd9'
        )
        
        resp = client.post(
            "/api/v1/suggestions/",
            data=_valid_create_params(),
            files={"photo": ("test.jpg", BytesIO(jpeg_bytes), "image/jpeg")},
            headers=_auth(token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["titulo"] == "Mejorar iluminación"
        
        # Verificar que foto_url es una URL válida de Google Cloud Storage
        foto_url = body["foto_url"]
        assert foto_url is not None, "foto_url debe estar presente"
        assert "https://storage.googleapis.com" in foto_url, f"Esperado URL de GCS en: {foto_url}"
        assert "multimedia_incidents/suggestions" in foto_url, f"Esperado prefijo correcto en: {foto_url}"
        assert foto_url.endswith((".jpg", ".jpeg", ".png")), f"Esperado extensión de imagen en: {foto_url}"

    def test_create_title_too_long_returns_422(self) -> None:
        """Valida longitud máxima de título (200 chars)."""
        token = _make_token(STUDENT_USER_ID, "Student")
        data = _valid_create_params()
        data["titulo"] = "x" * 201
        resp = client.post(
            "/api/v1/suggestions/",
            data=data,
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_create_empty_content_returns_400(self) -> None:
        """Valida que el contenido no esté vacío."""
        token = _make_token(STUDENT_USER_ID, "Student")
        data = _valid_create_params()
        data["contenido"] = "   "
        resp = client.post(
            "/api/v1/suggestions/",
            data=data,
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_create_missing_titulo_returns_422(self) -> None:
        """Valida que título es obligatorio."""
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.post(
            "/api/v1/suggestions/",
            data={"contenido": "Solo contenido sin título"},
            headers=_auth(token),
        )
        assert resp.status_code == 422

    def test_get_by_id_404(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.get(
            f"/api/v1/suggestions/{uuid4()}",
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_list_update_delete(self) -> None:
        """Test completo: crear, listar, actualizar y eliminar."""
        token = _make_token(STUDENT_USER_ID, "Student")
        
        # Crear sugerencia
        create = client.post(
            "/api/v1/suggestions/",
            data=_valid_create_params(),
            headers=_auth(token),
        )
        assert create.status_code == 201
        sid = create.json()["id"]

        # Listar
        listed = client.get("/api/v1/suggestions/", headers=_auth(token))
        assert listed.status_code == 200
        listed_body = listed.json()
        assert listed_body["total"] == 1
        assert len(listed_body["items"]) == 1

        # Actualizar
        upd = client.patch(
            f"/api/v1/suggestions/{sid}",
            json={"titulo": "Nuevo título"},
            headers=_auth(token),
        )
        assert upd.status_code == 200
        assert upd.json()["titulo"] == "Nuevo título"

        # Intentar actualizar con votos nulos (debe fallar)
        null_votes = client.patch(
            f"/api/v1/suggestions/{sid}",
            json={"total_votos": None},
            headers=_auth(token),
        )
        assert null_votes.status_code == 400
        detail = null_votes.json()["detail"]
        assert detail["error_code"] == "SUGGESTION_VALIDATION_ERROR"

        # Eliminar
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
        """Test listado de sugerencias populares ordenadas por votos."""
        token = _make_token(STUDENT_USER_ID, "Student")

        # Crear 3 sugerencias (sin votos inicialmente)
        suggestions = []
        for titulo in ["A", "B", "C"]:
            data = _valid_create_params()
            data["titulo"] = titulo
            resp = client.post(
                "/api/v1/suggestions/",
                data=data,
                headers=_auth(token),
            )
            assert resp.status_code == 201
            suggestions.append(resp.json())

        # B: 10 votos, C: 5 votos, A: 2 votos
        client.patch(
            f"/api/v1/suggestions/{suggestions[0]['id']}",
            json={"total_votos": 2},
            headers=_auth(token),
        )
        client.patch(
            f"/api/v1/suggestions/{suggestions[1]['id']}",
            json={"total_votos": 10},
            headers=_auth(token),
        )
        client.patch(
            f"/api/v1/suggestions/{suggestions[2]['id']}",
            json={"total_votos": 5},
            headers=_auth(token),
        )

        popular = client.get(
            "/api/v1/suggestions/popular?limit=2",
            headers=_auth(token),
        )
        assert popular.status_code == 200
        body = popular.json()
        assert len(body["items"]) == 2

        top = body["items"][0]
        assert top["titulo"] == "B"
        assert top["total_votos"] == 10
        assert "etiquetas" in top
        assert isinstance(top["etiquetas"], list)
        assert "created_at" in top

        second = body["items"][1]
        assert second["titulo"] == "C"
        assert second["total_votos"] == 5

    def test_popular_exposes_tags_and_date(self) -> None:
        """Las sugerencias populares incluyen etiquetas y fecha de publicación."""
        token = _make_token(STUDENT_USER_ID, "Student")

        data = _valid_create_params()
        data["etiquetas"] = "sostenibilidad,bienestar"
        resp = client.post("/api/v1/suggestions/", data=data, headers=_auth(token))
        assert resp.status_code == 201

        popular = client.get("/api/v1/suggestions/popular", headers=_auth(token))
        assert popular.status_code == 200
        item = popular.json()["items"][0]

        assert item["etiquetas"] == ["sostenibilidad", "bienestar"]
        assert item["created_at"] is not None

    def test_popular_rejects_invalid_limit(self) -> None:
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.get(
            "/api/v1/suggestions/popular?limit=0",
            headers=_auth(token),
        )
        assert resp.status_code == 422


class TestSuggestionMyHistory:
    def test_me_returns_empty_list_when_student_has_no_suggestions(self) -> None:
        token = _make_token(uuid4(), "Student")

        resp = client.get("/api/v1/suggestions/me", headers=_auth(token))

        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["total_pages"] == 0
        assert body["items"] == []

    def test_me_returns_only_authenticated_student_suggestions(self) -> None:
        student_a = uuid4()
        student_b = uuid4()
        token_a = _make_token(student_a, "Student")
        token_b = _make_token(student_b, "Student")

        payload_a = {
            "estudiante_id": str(student_a),
            "titulo": "Sugerencia A",
            "contenido": "Contenido A",
        }
        payload_b = {
            "estudiante_id": str(student_b),
            "titulo": "Sugerencia B",
            "contenido": "Contenido B",
        }

        assert (
            client.post(
                "/api/v1/suggestions/",
                json=payload_a,
                headers=_auth(token_a),
            ).status_code
            == 201
        )
        assert (
            client.post(
                "/api/v1/suggestions/",
                json=payload_b,
                headers=_auth(token_b),
            ).status_code
            == 201
        )

        resp_a = client.get("/api/v1/suggestions/me", headers=_auth(token_a))
        resp_b = client.get("/api/v1/suggestions/me", headers=_auth(token_b))

        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        body_a = resp_a.json()
        body_b = resp_b.json()

        assert body_a["total"] == 1
        assert body_b["total"] == 1
        assert body_a["items"][0]["estudiante_id"] == str(student_a)
        assert body_b["items"][0]["estudiante_id"] == str(student_b)

    def test_me_without_token_returns_401(self) -> None:
        resp = client.get("/api/v1/suggestions/me")
        assert resp.status_code == 401

    def test_me_with_non_student_role_returns_403(self) -> None:
        admin_token = _make_token(uuid4(), "Administrator")
        resp = client.get("/api/v1/suggestions/me", headers=_auth(admin_token))
        assert resp.status_code == 403

    def test_me_ignores_student_id_query_param(self) -> None:
        student = uuid4()
        other_student = uuid4()
        token = _make_token(student, "Student")

        assert (
            client.post(
                "/api/v1/suggestions/",
                json={
                    "estudiante_id": str(student),
                    "titulo": "Propia",
                    "contenido": "mia",
                },
                headers=_auth(token),
            ).status_code
            == 201
        )

        # Aunque se envíe un query param ajeno, la ruta /me debe usar el JWT.
        resp = client.get(
            f"/api/v1/suggestions/me?student_id={other_student}",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["estudiante_id"] == str(student)


class TestSuggestionFiltersAndSorting:
    """Pruebas de filtrado por etiquetas y ordenamiento del listado."""

    def _create(
        self,
        token: str,
        titulo: str,
        etiquetas: str | None = None,
        votos: int = 0,
    ) -> dict:
        data: dict = {"titulo": titulo, "contenido": f"Contenido de {titulo}"}
        if etiquetas:
            data["etiquetas"] = etiquetas
        resp = client.post("/api/v1/suggestions/", data=data, headers=_auth(token))
        assert resp.status_code == 201
        sid = resp.json()["id"]
        if votos:
            client.patch(
                f"/api/v1/suggestions/{sid}",
                json={"total_votos": votos},
                headers=_auth(token),
            )
        return resp.json()

    def test_order_by_fecha_default(self) -> None:
        """Sin parámetros, el orden por defecto es fecha descendente."""
        token = _make_token(STUDENT_USER_ID, "Student")
        self._create(token, "Primera")
        self._create(token, "Segunda")
        self._create(token, "Tercera")

        resp = client.get("/api/v1/suggestions/", headers=_auth(token))
        assert resp.status_code == 200
        titles = [i["titulo"] for i in resp.json()["items"]]
        # Las más recientes aparecen primero
        assert titles[0] == "Tercera"
        assert titles[-1] == "Primera"

    def test_order_by_popularidad(self) -> None:
        """order_by=popularidad ordena por votos descendentes."""
        token = _make_token(STUDENT_USER_ID, "Student")
        self._create(token, "Poca popularidad", votos=2)
        self._create(token, "Muy popular", votos=50)
        self._create(token, "Media popularidad", votos=20)

        resp = client.get(
            "/api/v1/suggestions/?order_by=popularidad",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert items[0]["titulo"] == "Muy popular"
        assert items[1]["titulo"] == "Media popularidad"
        assert items[2]["titulo"] == "Poca popularidad"

    def test_filter_by_single_tag(self) -> None:
        """Filtrar por una etiqueta sólo devuelve sugerencias con esa etiqueta."""
        token = _make_token(STUDENT_USER_ID, "Student")
        self._create(
            token, "Con infraestructura", etiquetas="infraestructura,seguridad"
        )
        self._create(token, "Con bienestar", etiquetas="bienestar")
        self._create(token, "Sin etiquetas")

        resp = client.get(
            "/api/v1/suggestions/?tags=infraestructura",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["titulo"] == "Con infraestructura"

    def test_filter_by_multiple_tags_returns_union(self) -> None:
        """Varios ?tags devuelven sugerencias con AL MENOS una etiqueta coincidente."""
        token = _make_token(STUDENT_USER_ID, "Student")
        self._create(token, "Solo infra", etiquetas="infraestructura")
        self._create(token, "Solo bienestar", etiquetas="bienestar")
        self._create(token, "Sin etiquetas")

        resp = client.get(
            "/api/v1/suggestions/?tags=infraestructura&tags=bienestar",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        titles = {i["titulo"] for i in body["items"]}
        assert titles == {"Solo infra", "Solo bienestar"}
        assert body["total"] == 2

    def test_filter_by_nonexistent_tag_returns_empty(self) -> None:
        """Filtrar por una etiqueta inexistente devuelve lista vacía."""
        token = _make_token(STUDENT_USER_ID, "Student")
        self._create(token, "Sugerencia normal", etiquetas="infraestructura")

        resp = client.get(
            "/api/v1/suggestions/?tags=inexistente",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_filter_and_order_combined(self) -> None:
        """Filtrar por etiqueta y ordenar por popularidad funcionan juntos."""
        token = _make_token(STUDENT_USER_ID, "Student")
        self._create(token, "Infra baja", etiquetas="infraestructura", votos=1)
        self._create(token, "Infra alta", etiquetas="infraestructura", votos=99)
        self._create(token, "Otro tag", etiquetas="bienestar", votos=50)

        resp = client.get(
            "/api/v1/suggestions/?tags=infraestructura&order_by=popularidad",
            headers=_auth(token),
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 2
        assert items[0]["titulo"] == "Infra alta"
        assert items[1]["titulo"] == "Infra baja"

    def test_invalid_order_by_returns_422(self) -> None:
        """Un valor inválido de order_by devuelve 422."""
        token = _make_token(STUDENT_USER_ID, "Student")
        resp = client.get(
            "/api/v1/suggestions/?order_by=invalido",
            headers=_auth(token),
        )
        assert resp.status_code == 422
