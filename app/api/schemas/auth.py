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


class ResendCodeRequest(BaseModel):
    """Payload para solicitar reenvío de código de verificación."""

    email: EmailStr


class ResendCodeResponse(BaseModel):
    """Respuesta tras solicitar reenvío de código."""

    message: str = "Si el correo está registrado, se ha enviado un nuevo código."

