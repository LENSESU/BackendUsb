from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    """Entidad de dominio: usuario del sistema."""

    id: int | None
    first_name: str
    last_name: str
    email: str
    password_hash: str
    role_id: int
    is_active: bool = True
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.first_name or not self.first_name.strip():
            raise ValueError("El nombre del usuario no puede estar vacío")

        if not self.last_name or not self.last_name.strip():
            raise ValueError("El apellido del usuario no puede estar vacío")

        if "@" not in self.email:
            raise ValueError("El email del usuario no es válido")

        if not self.password_hash:
            raise ValueError("El hash de contraseña no puede estar vacío")

