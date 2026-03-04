"""Rutas HTTP para autenticación por email/password."""

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt

from app.api.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.application.services import AuthService
from app.infrastructure.adapters import PostgresUserRepository

router = APIRouter()


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def _create_access_token(subject: UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
    try:
        user = await auth_service.login_or_register(
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    token = _create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.post(
    "/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Registro explícito de un usuario nuevo."""
    try:
        user = await auth_service.register(
            email=payload.email,
            password=payload.password,
            name=payload.name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    token = _create_access_token(user.id)
    return LoginResponse(access_token=token)
