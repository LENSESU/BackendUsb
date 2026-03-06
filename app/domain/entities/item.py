"""Entidad de dominio: Item.

Modificación para #63 (Validar accesos cruzados):
  Se añadió el campo ``owner_id`` para rastrear qué usuario creó cada item.
  Esto permite que la ruta DELETE valide si el solicitante es el dueño
  del recurso antes de permitir la eliminación.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Item:
    """Entidad de negocio Item. Sin dependencias de frameworks."""

    id: UUID
    name: str
    description: str | None = None
    # [NUEVO – #63] UUID del usuario que creó el item (ownership).
    # None para items legacy creados antes de la protección.
    owner_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("El nombre no puede estar vacío")
