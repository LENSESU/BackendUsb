"""Tests para los endpoints de registro y verificación OTP."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

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
    """La verificación debe retornar 400 si el OTP es incorrecto o expirado."""
    mock_user = MagicMock()
    mock_user.id = uuid4()

    with patch("app.api.routes.auth.get_db_session") as mock_session, \
         patch("app.api.routes.auth.OtpService") as mock_otp_service_class:

        mock_db = MagicMock()
        mock_db.scalar.return_value = mock_user
        mock_session.return_value = mock_db

        mock_otp_service = MagicMock()
        mock_otp_service.verify.return_value = False
        mock_otp_service_class.return_value = mock_otp_service

        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "email": "juan@correo.usbcali.edu.co",
                "code": "000000",
            },
        )

    assert response.status_code == 400
    assert "inválido" in response.json()["detail"].lower()