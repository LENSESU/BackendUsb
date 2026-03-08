"""Schemas de autenticación para login, logout y gestión de tokens."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Petición de login con credenciales."""
    
    email: str | None = None
    password: str | None = None


class TokenResponse(BaseModel):
    """Respuesta con los tokens de acceso y refresco."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = Field(
        ..., description="Segundos hasta que expire el access token"
    )


class RefreshTokenRequest(BaseModel):
    """Petición para refrescar un access token."""

    refresh_token: str


class TokenValidationRequest(BaseModel):
    """Petición para validar un token."""

    token: str


class TokenValidationResponse(BaseModel):
    """Respuesta de validación de token."""

    valid: bool
    error: str | None = None
    expired: bool = False
    message: str | None = None


class LogoutResponse(BaseModel):
    """Respuesta de logout exitoso."""

    message: str = "Sesión cerrada exitosamente"


class UserAuthInfo(BaseModel):
    """Información del usuario autenticado (extraída del token)."""

    user_id: UUID
    email: str
    role_id: UUID

    model_config = {"from_attributes": True}
