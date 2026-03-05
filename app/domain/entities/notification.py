from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Notification:
    """Entidad de dominio: notificación enviada a un usuario sobre un incidente."""

    id: UUID | None
    user_id: UUID
    incident_id: UUID
    message: str
    is_read: bool = False
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.message or not self.message.strip():
            raise ValueError("El mensaje de la notificación no puede estar vacío")
