"""Entidad de dominio: User."""

from dataclasses import dataclass
from enum import Enum


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"


@dataclass
class User:
    """Entidad de negocio User. Sin dependencias de frameworks."""

    id: int | None = None  # se asigna en la BD (autoincremental)
    email: str = ""
    password_hash: str = ""
    name: str | None = None
    role: UserRole = UserRole.STUDENT

    def __post_init__(self) -> None:
        if not self.email or not self.email.strip():
            raise ValueError("El email no puede estar vacío")
        if not self.password_hash:
            raise ValueError("El password_hash es obligatorio")

