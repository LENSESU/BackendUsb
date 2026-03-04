from dataclasses import dataclass


@dataclass(slots=True)
class Tag:
    """Entidad de dominio: etiqueta asociable a sugerencias."""

    id: int | None
    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la etiqueta no puede estar vacío")
