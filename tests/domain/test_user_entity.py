import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.entities.user import User


def test_user_entity_creates_successfully() -> None:
    """Caso de éxito: creación de usuario válida."""

    user_id = uuid4()
    role_id = uuid4()
    user = User(
        id=user_id,
        first_name="Juan",
        last_name="Pérez",
        email="juan@example.com",
        password_hash="hashed-password",
        role_id=role_id,
        is_active=True,
        created_at=datetime.utcnow(),
    )

    assert user.first_name == "Juan"
    assert user.is_active is True
    assert user.id == user_id
    assert user.role_id == role_id


@pytest.mark.parametrize("first_name", ["", "   "])
def test_user_entity_rejects_empty_first_name(first_name: str) -> None:
    """Caso límite: nombres de usuario vacíos o con solo espacios."""

    with pytest.raises(ValueError):
        User(
            id=None,
            first_name=first_name,
            last_name="Pérez",
            email="juan@example.com",
            password_hash="hashed-password",
            role_id=uuid4(),
        )


def test_user_entity_rejects_invalid_email() -> None:
    """Manejo de errores: email inválido."""

    with pytest.raises(ValueError):
        User(
            id=None,
            first_name="Juan",
            last_name="Pérez",
            email="no-es-email",
            password_hash="hashed-password",
            role_id=uuid4(),
        )

