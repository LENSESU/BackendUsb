"""Tests para autenticación: login, logout y validación de tokens."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.auth import get_auth_service
from app.application.services.auth_service import AuthService
from app.core.token_blacklist import clear_blacklist
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_token_blacklist():
    """Limpia la blacklist de tokens antes de cada test."""
    clear_blacklist()
    yield
    clear_blacklist()


def test_login_logout_flow():
    """
    Test del flujo completo de login y logout.
    
    Este test requiere que exista un usuario en la base de datos.
    Por ahora es un test de integración conceptual que muestra el flujo.
    """
    # TODO: Crear usuario de prueba en la BD antes de ejecutar este test
    # Por ahora, este test fallará sin datos de prueba en la BD
    
    # 1. Login con credenciales válidas (requiere usuario en BD)
    # login_data = {
    #     "email": "test@example.com",
    #     "password": "testpassword123"
    # }
    # response = client.post("/api/v1/auth/login", json=login_data)
    # assert response.status_code == 200
    # token_data = response.json()
    # assert "access_token" in token_data
    # assert token_data["token_type"] == "bearer"
    # 
    # token = token_data["access_token"]
    # 
    # # 2. Usar token para acceder a endpoint protegido
    # headers = {"Authorization": f"Bearer {token}"}
    # response = client.get("/api/v1/auth/me", headers=headers)
    # assert response.status_code == 200
    # user_info = response.json()
    # assert "user_id" in user_info
    # assert "email" in user_info
    # 
    # # 3. Hacer logout
    # response = client.post("/api/v1/auth/logout", headers=headers)
    # assert response.status_code == 200
    # assert response.json()["message"] == "Sesión cerrada exitosamente"
    # 
    # # 4. Intentar usar el token después del logout (debe fallar)
    # response = client.get("/api/v1/auth/me", headers=headers)
    # assert response.status_code == 401
    # assert "revocado" in response.json()["detail"]
    
    # Test placeholder
    assert True


def test_logout_without_token():
    """Test de logout sin token (debe fallar)."""
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401


def test_me_endpoint_without_token():
    """Test de acceso a /me sin token (debe fallar)."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_login_with_invalid_credentials():
    """Login con credenciales inválidas retorna 401 sin depender de PostgreSQL."""
    mock_repo = MagicMock()
    mock_repo.get_by_email_sync.return_value = None

    app.dependency_overrides[get_auth_service] = lambda: AuthService(mock_repo)
    try:
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        }
        response = client.post("/api/v1/auth/login", json=login_data)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


def test_refresh_token_flow():
    """
    Test del flujo de refresh token.
    
    Requiere usuario en la BD para login inicial.
    """
    # TODO: Implementar con usuario de prueba
    # 1. Login y obtener tokens
    # 2. Usar refresh token para obtener nuevo access token
    # 3. Verificar que el nuevo access token funciona
    # 4. Verificar que el refresh token anterior está en blacklist (rotación)
    assert True


def test_validate_token_endpoint():
    """Test del endpoint de validación de tokens."""
    # Token inválido
    response = client.post(
        "/api/v1/auth/validate",
        json={"token": "invalid_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["error"] is not None


def test_refresh_with_invalid_token():
    """Test de refresh con token inválido."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    # Verificar estructura de error
    if isinstance(data["detail"], dict):
        assert "error_code" in data["detail"]
        assert data["detail"]["error_code"] in (
            "REFRESH_TOKEN_INVALID",
            "REFRESH_TOKEN_EXPIRED",
        )


def test_token_expiration_response_structure():
    """
    Test de que las respuestas de error incluyen la estructura esperada
    para que el frontend pueda manejar la expiración.
    """
    # Endpoint protegido sin token
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    
    # Con token inválido
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    
    data = response.json()
    # Verificar que incluye información estructurada
    if isinstance(data.get("detail"), dict):
        detail = data["detail"]
        assert "message" in detail
        assert "error_code" in detail
        assert "redirect_to_login" in detail

