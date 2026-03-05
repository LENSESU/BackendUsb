from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Otp:
    """Entidad de dominio: código OTP para verificación de cuenta."""

    id: UUID | None
    user_id: UUID
    code: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ValueError("El código OTP no puede estar vacío")

        if len(self.code) != 6:
            raise ValueError("El código OTP debe tener exactamente 6 caracteres")

        if not self.code.isdigit():
            raise ValueError("El código OTP debe contener solo dígitos")

    @property
    def is_active(self) -> bool:
        """Retorna True si el OTP no ha sido consumido (soft delete)."""
        return self.deleted_at is None
