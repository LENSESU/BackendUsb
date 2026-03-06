"""Tests para los endpoints de registro y verificación OTP."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies.otp import get_otp_service
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# /register
# ---------------------------------------------------------------------------


def test_register_rejects_invalid_email_domain() -> None:
    """El registro debe rechazar dominios de correo no permitidos."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "juan@gmail.com",
            "password": "password123",
            "role_id": str(uuid4()),
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any("dominio" in str(e).lower() for e in detail)


def test_register_rejects_invalid_email_format() -> None:
    """El registro debe rechazar emails con formato inválido."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Juan",
            "last_name": "Pérez",
            "email": "no-es-un-email",
            "password": "password123",
            "role_id": str(uuid4()),
        },
    )
    assert response.status_code == 422


def test_register_rejects_missing_fields() -> None:
    """El registro debe rechazar requests con campos obligatorios ausentes."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "juan@correo.usbcali.edu.co",
            "password": "password123",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# /verify-otp
# ---------------------------------------------------------------------------


def test_verify_otp_rejects_invalid_email_format() -> None:
    """La verificación debe rechazar emails con formato inválido."""
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "no-es-email", "code": "123456"},
    )
    assert response.status_code == 422


def test_verify_otp_returns_404_for_unknown_email() -> None:
    """La verificación debe retornar 404 si el email no existe en BD."""
    with patch(
        "app.api.routes.auth.get_db_session"
    ) as mock_session:
        mock_db = MagicMock()
        mock_db.scalar.return_value = None
        mock_session.return_value = mock_db

        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "email": "noexiste@correo.usbcali.edu.co",
                "code": "123456",
            },
        )

    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()


def test_verify_otp_returns_400_for_invalid_code() -> None:
    mock_user = MagicMock()
    mock_user.id = uuid4()

    # Mock del OtpService que devolverá verify=False
    mock_otp_service = MagicMock()
    mock_otp_service.verify.return_value = False

    with patch("app.api.routes.auth.get_db_session") as mock_session:
        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_user
        mock_session.return_value = mock_db

        # ← Así se override una dependencia de FastAPI en tests
        app.dependency_overrides[get_otp_service] = lambda: mock_otp_service

        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "email": "juan@correo.usbcali.edu.co",
                "code": "000000",
            },
        )

        app.dependency_overrides.clear()  # limpiar después del test

    assert response.status_code == 400
    assert "inválido" in response.json()["detail"].lower()

# ---------------------------------------------------------------------------
# /resend-otp
# ---------------------------------------------------------------------------

def test_resend_otp_returns_404_for_unknown_email() -> None:
    """El reenvío debe retornar 404 si el email no existe en BD."""
    with patch("app.api.routes.auth.get_db_session") as mock_session:
        mock_db = MagicMock()
        mock_db.scalar.return_value = None
        mock_session.return_value = mock_db

        response = client.post(
            "/api/v1/auth/resend-otp",
            json={"email": "noexiste@correo.usbcali.edu.co"},
        )

    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()


def test_resend_otp_returns_429_during_cooldown() -> None:
    """El reenvío debe retornar 429 si el cooldown no ha pasado."""
    mock_user = MagicMock()
    mock_user.id = uuid4()

    mock_otp_service = MagicMock()
    mock_otp_service.resend = AsyncMock(side_effect=ValueError("Debes esperar 12 segundos antes de reenviar"))

    with patch("app.api.routes.auth.get_db_session") as mock_session:
        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_user
        mock_session.return_value = mock_db

        app.dependency_overrides[get_otp_service] = lambda: mock_otp_service
        response = client.post(
            "/api/v1/auth/resend-otp",
            json={"email": "juan@correo.usbcali.edu.co"},
        )
        app.dependency_overrides.clear()

    assert response.status_code == 429
    assert "esperar" in response.json()["detail"].lower()


def test_resend_otp_returns_400_when_no_active_otp() -> None:
    """El reenvío debe retornar 400 si no hay OTP activo para el usuario."""
    mock_user = MagicMock()
    mock_user.id = uuid4()

    mock_otp_service = MagicMock()
    mock_otp_service.resend = AsyncMock(side_effect=ValueError("No hay un OTP activo para este usuario"))

    with patch("app.api.routes.auth.get_db_session") as mock_session:
        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_user
        mock_session.return_value = mock_db

        app.dependency_overrides[get_otp_service] = lambda: mock_otp_service
        response = client.post(
            "/api/v1/auth/resend-otp",
            json={"email": "juan@correo.usbcali.edu.co"},
        )
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "otp activo" in response.json()["detail"].lower()