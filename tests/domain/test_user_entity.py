import pytest
from datetime import datetime

from app.domain.entities.user import User


def test_user_entity_creates_successfully() -> None:
    """Caso de éxito: creación de usuario válida."""

    user = User(
        id=1,
        first_name="Juan",
        last_name="Pérez",
        email="juan@example.com",
        password_hash="hashed-password",
        role_id=2,
        is_active=True,
        created_at=datetime.utcnow(),
    )

    assert user.first_name == "Juan"
    assert user.is_active is True


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
            role_id=1,
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
            role_id=1,
        )

