from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class Vote:
    """Entidad de dominio: voto de un estudiante a una sugerencia."""

    id: UUID | None
    student_id: UUID
    suggestion_id: UUID
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.student_id is None:
            raise ValueError("El voto debe estar asociado a un estudiante")

        if self.suggestion_id is None:
            raise ValueError("El voto debe estar asociado a una sugerencia")
