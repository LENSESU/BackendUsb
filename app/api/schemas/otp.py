"""Schemas para registro de usuario y verificación de OTP."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.core.config import settings


class RegisterRequest(BaseModel):
    """Petición de registro de nuevo usuario."""

    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role_id: UUID

    @field_validator("email")
    @classmethod
    def email_domain_allowed(cls, value: str) -> str:
        domain = value.split("@")[-1]
        if domain not in settings.allowed_email_domains:
            allowed = ", ".join(f"@{d}" for d in settings.allowed_email_domains)
            msg = f"El correo debe pertenecer a uno de estos dominios: {allowed}"
            raise ValueError(msg)
        return value


class OtpSentResponse(BaseModel):
    """Respuesta tras enviar un OTP al correo del usuario."""

    message: str = "Código de verificación enviado a tu correo"


class VerifyOtpRequest(BaseModel):
    """Petición para verificar el OTP recibido por email."""

    email: EmailStr
    code: str
