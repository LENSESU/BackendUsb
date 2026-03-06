"""Tests para la entidad de dominio Otp."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.entities.otp import Otp


def test_otp_entity_creates_successfully() -> None:
    """Caso de éxito: creación de OTP válida."""
    otp = Otp(
        id=uuid4(),
        user_id=uuid4(),
        code="123456",
    )

    assert otp.code == "123456"
    assert otp.deleted_at is None
    assert otp.is_active is True


def test_otp_is_inactive_when_soft_deleted() -> None:
    """Un OTP con deleted_at definido debe reportarse como inactivo."""
    otp = Otp(
        id=uuid4(),
        user_id=uuid4(),
        code="654321",
        deleted_at=datetime.now(UTC),
    )

    assert otp.is_active is False


@pytest.mark.parametrize("code", ["", "   "])
def test_otp_entity_rejects_empty_code(code: str) -> None:
    """Caso límite: código vacío o con solo espacios."""
    with pytest.raises(ValueError):
        Otp(id=None, user_id=uuid4(), code=code)


@pytest.mark.parametrize("code", ["12345", "1234567"])
def test_otp_entity_rejects_invalid_length(code: str) -> None:
    """Caso límite: código que no tiene exactamente 6 caracteres."""
    with pytest.raises(ValueError):
        Otp(id=None, user_id=uuid4(), code=code)


@pytest.mark.parametrize("code", ["abc123", "12 456", "!@#$%^"])
def test_otp_entity_rejects_non_numeric_code(code: str) -> None:
    """Caso límite: código que contiene caracteres no numéricos."""
    with pytest.raises(ValueError):
        Otp(id=None, user_id=uuid4(), code=code)