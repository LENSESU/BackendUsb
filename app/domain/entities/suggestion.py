from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Suggestion:
    """Entidad de dominio: sugerencia de mejora enviada por un estudiante."""

    id: int | None
    student_id: int
    title: str
    content: str
    photo_id: int | None = None
    total_votes: int = 0
    institutional_comment: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("El título de la sugerencia no puede estar vacío")

        if not self.content or not self.content.strip():
            raise ValueError("El contenido de la sugerencia no puede estar vacío")

        if self.total_votes < 0:
            raise ValueError("El total de votos no puede ser negativo")
