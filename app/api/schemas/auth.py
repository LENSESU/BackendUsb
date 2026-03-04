"""Esquemas Pydantic para la API de autenticación."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Payload para login / registro automático."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Payload para registro explícito de usuario."""

    email: EmailStr
    password: str
    name: str | None = None


class LoginResponse(BaseModel):
    """Respuesta tras autenticación / registro."""

    access_token: str
    token_type: str = "bearer"
