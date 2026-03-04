"""Servicio para generar y reenviar códigos de verificación (ej. email)."""

import logging
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Almacén en memoria: email -> {"code": str, "expires_at": datetime}
_store: dict[str, dict[str, Any]] = {}
CODE_LENGTH = 6
EXPIRY_MINUTES = 10


def _generate_code() -> str:
    return "".join(random.choices(string.digits, k=CODE_LENGTH))


def generate_and_store(email: str) -> str:
    """Genera un código, lo guarda asociado al email y lo devuelve (para enviar por email o log)."""
    code = _generate_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=EXPIRY_MINUTES)
    _store[email.lower().strip()] = {"code": code, "expires_at": expires_at}
    return code


def get_stored_code(email: str) -> str | None:
    """Devuelve el código vigente para el email, o None si no existe o expiró."""
    key = email.lower().strip()
    if key not in _store:
        return None
    data = _store[key]
    if datetime.now(timezone.utc) >= data["expires_at"]:
        del _store[key]
        return None
    return data["code"]


def invalidate_code(email: str) -> None:
    """Elimina el código guardado para ese email."""
    _store.pop(email.lower().strip(), None)
