from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.schemas.user import UserCreate, UserResponse


def test_user_create_schema_ok() -> None:
    """Caso de éxito: payload válido para crear usuario."""

    role_id = uuid4()
    payload = {
        "first_name": "Ana",
        "last_name": "García",
        "email": "ana@example.com",
        "password": "supersegura",
        "role_id": str(role_id),
    }

    schema = UserCreate(**payload)

    assert schema.first_name == "Ana"
    assert schema.role_id == role_id


def test_user_create_schema_invalid_email() -> None:
    """Manejo de errores: email inválido en schema Pydantic."""

    role_id = uuid4()
    payload = {
        "first_name": "Ana",
        "last_name": "García",
        "email": "no-email",
        "password": "supersegura",
        "role_id": str(role_id),
    }

    with pytest.raises(ValidationError):
        UserCreate(**payload)


def test_user_response_from_attributes() -> None:
    """Ejemplo: construcción de respuesta desde atributos de entidad de dominio."""

    user_id = uuid4()
    role_id = uuid4()

    class FakeUser:
        """Objeto simulado que imita una entidad de dominio."""

        def __init__(self) -> None:
            self.id = user_id
            self.first_name = "Ana"
            self.last_name = "García"
            self.email = "ana@example.com"
            self.role_id = role_id
            self.is_active = True
            self.created_at = datetime.utcnow()

    entity = FakeUser()
    response = UserResponse.model_validate(entity)

    assert response.id == user_id
    assert response.role_id == role_id
    assert response.is_active is True
