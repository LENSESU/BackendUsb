from dataclasses import dataclass


@dataclass(slots=True)
class Role:
    """Entidad de dominio: rol de usuario en el sistema."""

    id: int | None
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre del rol no puede estar vacío")

