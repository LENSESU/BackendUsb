"""Manejadores globales de excepciones para respuestas consistentes."""

import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_response(detail: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "status_code": status_code},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convierte excepciones de dominio/aplicación a respuesta JSON."""
    return _error_response(exc.message, exc.status_code)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Formato consistente para errores de validación Pydantic (422)."""
    errors = [
        {
            "loc": list(e.get("loc", [])),
            "msg": e.get("msg", ""),
            "type": e.get("type"),
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": errors, "status_code": 422},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura excepciones no manejadas; reexpone HTTPException de FastAPI."""
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "status_code": exc.status_code},
        )
    logger.exception("Error no controlado: %s", exc)
    return _error_response(
        "Error interno del servidor",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
