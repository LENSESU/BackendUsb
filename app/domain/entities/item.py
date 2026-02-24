"""Entidad de dominio: Item."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Item:
    """Entidad de negocio Item. Sin dependencias de frameworks."""

    id: UUID
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre no puede estar vacío")
