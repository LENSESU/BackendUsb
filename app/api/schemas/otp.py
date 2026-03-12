"""Schemas para registro de usuario y verificación de OTP."""

import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.core.config import settings


NAME_PATTERN = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü]+(?:[ '-][A-Za-zÁÉÍÓÚáéíóúÑñÜü]+)*$")
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&._\-])[A-Za-z\d@$!%*?&._\-]{8,}$"
)


class RegisterRequest(BaseModel):
    """Petición de registro de nuevo usuario."""

    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def email_domain_allowed(cls, value: str) -> str:
        domain = value.split("@")[-1]
        if domain not in settings.allowed_email_domains:
            allowed = ", ".join(f"@{d}" for d in settings.allowed_email_domains)
            msg = f"El correo debe pertenecer a uno de estos dominios: {allowed}"
            raise ValueError(msg)
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        trimmed_value = value.strip()
        if len(trimmed_value) < 2:
            raise ValueError("Debe tener al menos 2 caracteres")
        if not NAME_PATTERN.match(trimmed_value):
            raise ValueError(
                "Solo puede contener letras, espacios, apóstrofes o guiones"
            )
        return trimmed_value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(
                "La contraseña debe tener mínimo 8 caracteres, mayúscula, "
                "minúscula, número y símbolo"
            )
        return value


class OtpSentResponse(BaseModel):
    """Respuesta tras enviar un OTP al correo del usuario."""

    message: str = "Código de verificación enviado a tu correo"


class VerifyOtpRequest(BaseModel):
    """Petición para verificar el OTP recibido por email."""

    email: EmailStr
    code: str


class ResendOtpRequest(BaseModel):
    """Petición para reenviar el OTP."""

    email: EmailStr
