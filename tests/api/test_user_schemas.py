from datetime import datetime

import pytest
from pydantic import ValidationError

from app.api.schemas.user import UserCreate, UserResponse


def test_user_create_schema_ok() -> None:
    """Caso de éxito: payload válido para crear usuario."""

    payload = {
        "first_name": "Ana",
        "last_name": "García",
        "email": "ana@example.com",
        "password": "supersegura",
        "role_id": 1,
    }

    schema = UserCreate(**payload)

    assert schema.first_name == "Ana"
    assert schema.role_id == 1


def test_user_create_schema_invalid_email() -> None:
    """Manejo de errores: email inválido en schema Pydantic."""

    payload = {
        "first_name": "Ana",
        "last_name": "García",
        "email": "no-email",
        "password": "supersegura",
        "role_id": 1,
    }

    with pytest.raises(ValidationError):
        UserCreate(**payload)


def test_user_response_from_attributes() -> None:
    """Ejemplo: construcción de respuesta desde atributos de entidad de dominio."""

    class FakeUser:
        """Objeto simulado que imita una entidad de dominio."""

        def __init__(self) -> None:
            self.id = 1
            self.first_name = "Ana"
            self.last_name = "García"
            self.email = "ana@example.com"
            self.role_id = 1
            self.is_active = True
            self.created_at = datetime.utcnow()

    entity = FakeUser()
    response = UserResponse.model_validate(entity)

    assert response.id == 1
    assert response.is_active is True

