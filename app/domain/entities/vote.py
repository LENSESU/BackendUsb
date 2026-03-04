from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Vote:
    """Entidad de dominio: voto de un estudiante a una sugerencia."""

    id: int | None
    student_id: int
    suggestion_id: int
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.student_id:
            raise ValueError("El voto debe estar asociado a un estudiante")

        if not self.suggestion_id:
            raise ValueError("El voto debe estar asociado a una sugerencia")
