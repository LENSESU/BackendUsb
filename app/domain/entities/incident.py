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


def incident_status_as_str(value: str | IncidentStatus) -> str:
    """Normaliza un estado recibido (enum o cadena) al valor almacenado."""
    return value.value if isinstance(value, IncidentStatus) else value


def is_known_incident_status(value: str) -> bool:
    """Indica si ``value`` coincide con uno de los estados del dominio."""
    try:
        IncidentStatus(value)
    except ValueError:
        return False
    return True


# Transiciones válidas del ciclo de vida (flujo lineal sin re-apertura).
ALLOWED_INCIDENT_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    IncidentStatus.NUEVO.value: frozenset({IncidentStatus.EN_PROCESO.value}),
    IncidentStatus.EN_PROCESO.value: frozenset({IncidentStatus.RESUELTO.value}),
    IncidentStatus.RESUELTO.value: frozenset(),
}


def validate_incident_status_transition(current: str, new: str) -> None:
    """Comprueba que pasar de ``current`` a ``new`` sea una transición permitida.

    Raises:
        ValueError: estado destino desconocido, origen inconsistente o transición
            no listada en ``ALLOWED_INCIDENT_STATUS_TRANSITIONS``.
    """
    if current == new:
        return
    if not is_known_incident_status(new):
        allowed = ", ".join(s.value for s in IncidentStatus)
        raise ValueError(
            f"Estado de incidente no válido: {new!r}. Valores permitidos: {allowed}."
        )
    if not is_known_incident_status(current):
        raise ValueError(
            f"El incidente tiene un estado almacenado no reconocido ({current!r}). "
            "Corrija el registro antes de cambiar el estado."
        )
    allowed_next = ALLOWED_INCIDENT_STATUS_TRANSITIONS[current]
    if new not in allowed_next:
        if not allowed_next:
            raise ValueError(
                f"No se puede cambiar el estado desde {current!r} "
                "(estado final del flujo)."
            )
        opts = ", ".join(sorted(allowed_next))
        raise ValueError(
            f"Transición de estado no permitida: {current!r} → {new!r}. "
            f"Desde {current!r} solo se admite: {opts}."
        )


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
