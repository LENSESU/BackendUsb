"""Esquemas de respuesta para errores (formato consistente)."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Un solo error (ej. campo de validación)."""

    loc: list[str] | None = None
    msg: str
    type: str | None = None


class ErrorResponse(BaseModel):
    """Respuesta estándar de error de la API."""

    detail: str | list[ErrorDetail]  # mensaje único o lista de errores de validación
    status_code: int | None = None
