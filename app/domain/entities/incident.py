from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class IncidentLocation:
    """Valor de dominio para ubicación de un incidente."""

    campus_place: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(slots=True)
class Incident:
    """Entidad de dominio: incidente reportado por un estudiante."""

    id: UUID | None
    student_id: UUID
    technician_id: UUID | None
    category_id: UUID
    description: str
    before_photo_id: UUID
    after_photo_id: UUID | None = None
    status: str = "Nuevo"
    priority: str | None = None
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

        if self.before_photo_id is None:
            raise ValueError("El incidente debe tener una foto 'antes'")
