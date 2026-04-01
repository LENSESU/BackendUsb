"""Manejadores globales de excepciones para respuestas consistentes."""

import logging

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


def _error_response(
    message: str,
    status_code: int,
    error_code: str | None = None,
    errors: list[dict] | None = None,
) -> JSONResponse:
    content: dict = {
        "message": message,
        "error_code": error_code or "GENERIC_ERROR",
        "status_code": status_code,
    }
    if errors is not None:
        content["errors"] = errors
    return JSONResponse(
        status_code=status_code,
        content=content,
         headers={                                                    # 👈 agrega esto
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Credentials": "true",
        },
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convierte excepciones de dominio/aplicación a respuesta JSON."""
    return _error_response(
        message=exc.message,
        status_code=exc.status_code,
        error_code="APP_ERROR",
    )


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
    return _error_response(
        message="Error de validación en la solicitud",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="REQUEST_VALIDATION_ERROR",
        errors=errors,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Captura excepciones no manejadas; reexpone HTTPException de FastAPI."""
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, dict):
            return _error_response(
                message=detail.get("message", "Solicitud inválida"),
                status_code=exc.status_code,
                error_code=detail.get("error_code", "HTTP_ERROR"),
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": str(detail),
                "error_code": "HTTP_ERROR",
                "status_code": exc.status_code,
            },
        )
    logger.exception("Error no controlado: %s", exc)
    return _error_response(
        message="Error interno del servidor",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
    )
