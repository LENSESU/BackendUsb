"""Entidad de dominio: User."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class User:
    """Entidad de negocio User. Sin dependencias de frameworks."""

    id: UUID
    email: str
    password_hash: str
    name: str | None = None

    def __post_init__(self) -> None:
        if not self.email or not self.email.strip():
            raise ValueError("El email no puede estar vacío")
        if not self.password_hash:
            raise ValueError("El password_hash es obligatorio")
