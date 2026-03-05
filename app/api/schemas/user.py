"""Esquemas Pydantic para la API de Usuarios."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Payload para crear un usuario."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role_id: UUID = Field(...)


class UserUpdate(BaseModel):
    """Payload para actualizar datos de un usuario."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    role_id: UUID | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Respuesta con datos de un usuario."""

    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    role_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
