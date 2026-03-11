"""Tests para el endpoint de categorías de incidentes."""
import pytest
from unittest.mock import MagicMock
from uuid import UUID, uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.incident_category import get_service
from app.application.services.incident_category_service import IncidentCategoryService
from app.domain.entities.incident_category import IncidentCategory

client = TestClient(app)

# Categorías de prueba
FAKE_CATEGORIES = [
    IncidentCategory(id=UUID("4caad060-d2bd-46a2-90fa-ad834243c8a7"), name="Infraestructura", description="Daños en infraestructura"),
    IncidentCategory(id=UUID("5b37c257-4f97-469b-bb9a-51a243d2b0c9"), name="Eléctrico", description="Problemas eléctricos"),
]


def mock_service_with_data():
    """Servicio mockeado con categorías de prueba."""
    service = MagicMock(spec=IncidentCategoryService)
    service.get_all_categories.return_value = FAKE_CATEGORIES
    service.validate_category_id.return_value = FAKE_CATEGORIES[0]
    return service


def mock_service_empty():
    """Servicio mockeado sin categorías."""
    service = MagicMock(spec=IncidentCategoryService)
    service.get_all_categories.return_value = []
    return service


def mock_service_invalid_id():
    """Servicio mockeado que lanza error por ID inválido."""
    service = MagicMock(spec=IncidentCategoryService)
    service.validate_category_id.side_effect = ValueError("La categoría no existe.")
    return service


# --- Tests GET /incident-categories/ ---

def test_listar_categorias_retorna_200():
    """Debe retornar 200 con lista de categorías."""
    app.dependency_overrides[get_service] = mock_service_with_data
    response = client.get("/api/v1/incident-categories/")
    app.dependency_overrides.clear()
    assert response.status_code == 200


def test_listar_categorias_retorna_lista():
    """Debe retornar una lista con las categorías."""
    app.dependency_overrides[get_service] = mock_service_with_data
    response = client.get("/api/v1/incident-categories/")
    app.dependency_overrides.clear()
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_listar_categorias_estructura_correcta():
    """Cada categoría debe tener id, name y description."""
    app.dependency_overrides[get_service] = mock_service_with_data
    response = client.get("/api/v1/incident-categories/")
    app.dependency_overrides.clear()
    categoria = response.json()[0]
    assert "id" in categoria
    assert "name" in categoria
    assert "description" in categoria


def test_listar_categorias_lista_vacia():
    """Debe retornar 200 con lista vacía si no hay categorías."""
    app.dependency_overrides[get_service] = mock_service_empty
    response = client.get("/api/v1/incident-categories/")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# --- Tests GET /incident-categories/{category_id} ---

def test_obtener_categoria_valida_retorna_200():
    """Debe retornar 200 con una categoría válida."""
    app.dependency_overrides[get_service] = mock_service_with_data
    response = client.get("/api/v1/incident-categories/4caad060-d2bd-46a2-90fa-ad834243c8a7")
    app.dependency_overrides.clear()
    assert response.status_code == 200


def test_obtener_categoria_valida_retorna_datos():
    """Debe retornar los datos correctos de la categoría."""
    app.dependency_overrides[get_service] = mock_service_with_data
    response = client.get("/api/v1/incident-categories/4caad060-d2bd-46a2-90fa-ad834243c8a7")
    app.dependency_overrides.clear()
    data = response.json()
    assert data["name"] == "Infraestructura"


def test_obtener_categoria_id_invalido_retorna_404():
    """Debe retornar 404 si el category_id no existe."""
    app.dependency_overrides[get_service] = mock_service_invalid_id
    response = client.get(f"/api/v1/incident-categories/{uuid4()}")
    app.dependency_overrides.clear()
    assert response.status_code == 404


def test_obtener_categoria_404_incluye_detalle():
    """El 404 debe incluir un mensaje de error."""
    app.dependency_overrides[get_service] = mock_service_invalid_id
    response = client.get(f"/api/v1/incident-categories/{uuid4()}")
    app.dependency_overrides.clear()
    assert "detail" in response.json()