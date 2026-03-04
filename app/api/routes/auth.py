"""Rutas HTTP para autenticación por email/password."""

import logging
from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends
from jose import jwt

from app.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    ResendCodeRequest,
    ResendCodeResponse,
)
from app.application.services import AuthService
from app.application.services.verification_code_service import generate_and_store
from app.infrastructure.adapters import PostgresUserRepository

logger = logging.getLogger(__name__)

router = APIRouter()


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def _create_access_token(subject: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_auth_service() -> AuthService:
    """Obtiene el servicio de autenticación."""
    repository = PostgresUserRepository()
    return AuthService(user_repository=repository)


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    user = await auth_service.login_or_register(
        email=payload.email,
        password=payload.password,
    )
    token = _create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Registro explícito de un usuario nuevo."""
    user = await auth_service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    token = _create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.post("/resend-code", response_model=ResendCodeResponse)
async def resend_code(payload: ResendCodeRequest) -> ResendCodeResponse:
    """Genera y almacena un nuevo código de verificación para el email.
    En desarrollo el código se registra en logs; en producción se enviaría por email.
    """
    code = generate_and_store(payload.email)
    logger.info("Código de verificación para %s: %s", payload.email, code)
    return ResendCodeResponse()
