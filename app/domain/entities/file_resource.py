from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class FileResource:
    """Entidad de dominio: archivo asociado a incidentes o sugerencias."""

    id: int | None
    url: str
    file_type: str | None = None
    uploaded_by_user_id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.url or not self.url.strip():
            raise ValueError("La URL del archivo no puede estar vacía")

