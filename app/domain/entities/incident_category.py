from dataclasses import dataclass


@dataclass(slots=True)
class IncidentCategory:
    """Entidad de dominio: categoría de incidente."""

    id: int | None
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la categoría no puede estar vacío")

