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
from uuid import UUID


@dataclass(slots=True)
class IncidentLocation:
    """Valor de dominio (Value Object) para la ubicación de un incidente.

    Todos los campos son opcionales; se crea solo si el cliente envía
    al menos un dato de ubicación.
    """

    campus_place: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(slots=True)
class Incident:
    """Entidad de dominio: incidente reportado por un usuario.

    Campos requeridos (sin default) van primero por restricción de
    ``dataclass(slots=True)``.

    Campos automáticos (#107):
      - ``student_id``: se asigna desde el JWT del usuario autenticado.
      - ``created_at``: se asigna con la hora UTC del servidor.
      - ``status``: inicia en ``"Nuevo"`` (default de la entidad).
    """

    # --- Campos requeridos (sin default) ---
    id: UUID | None
    student_id: UUID              # [#107] UUID del usuario que reporta (desde JWT)
    technician_id: UUID | None    # Técnico asignado (None al crear)
    category_id: UUID             # Categoría del incidente
    description: str              # Descripción textual
    before_photo_id: UUID         # Foto "antes" (requerida)

    # --- Campos con default ---
    status: str = "Nuevo"                     # [#107] Estado inicial por defecto
    priority: str | None = None               # Prioridad opcional
    after_photo_id: UUID | None = None        # Foto "después" (opcional)
    created_at: datetime | None = None        # [#107] Lo asigna IncidentService
    updated_at: datetime | None = None        # Se actualiza en futuras ediciones
    location: IncidentLocation | None = None  # Ubicación opcional

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValueError("La descripción del incidente no puede estar vacía")

        if self.student_id is None:
            raise ValueError("El incidente debe tener un estudiante asociado")

        if self.category_id is None:
            raise ValueError("El incidente debe tener una categoría asociada")

        if self.before_photo_id is None:
            raise ValueError("El incidente debe tener una foto 'antes'")
