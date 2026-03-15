"""Entidad de dominio: Incidente.

Define la estructura y validaciones de negocio de un incidente
reportado por un usuario del sistema.

Cambios relevantes para HU-E2-011:
  - Se reordenó ``before_photo_id`` antes de los campos con valor por
    defecto para cumplir con la restricción de ``dataclass(slots=True)``
    en Python 3.11+ (los campos sin default deben ir primero).
  - ``status`` tiene valor por defecto ``"Nuevo"`` — es el estado inicial
    que esperan las tareas #107 y #109.
  - ``created_at`` se deja como ``None`` en la entidad; el servicio
    (``IncidentService``) lo asigna con la hora del servidor (#107).
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class IncidentStatus(StrEnum):
    """Estados permitidos para un incidente."""

    NUEVO = "Nuevo"
    EN_PROCESO = "En_proceso"
    RESUELTO = "Resuelto"


@dataclass(slots=True)
class IncidentLocation:
    campus_place: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(slots=True)
class Incident:
    id: UUID | None
    student_id: UUID
    technician_id: UUID | None
    category_id: UUID
    description: str
    before_photo_id: UUID | None = None
    status: str = IncidentStatus.NUEVO.value
    priority: str | None = None
    after_photo_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    location: IncidentLocation | None = None

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValueError("La descripción del incidente no puede estar vacía")

        if self.student_id is None:
            raise ValueError("El incidente debe tener un estudiante asociado")

        if self.category_id is None:
            raise ValueError("El incidente debe tener una categoría asociada")
