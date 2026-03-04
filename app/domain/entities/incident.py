from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class IncidentLocation:
    """Valor de dominio para ubicación de un incidente."""

    campus_place: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(slots=True)
class Incident:
    """Entidad de dominio: incidente reportado por un estudiante."""

    id: int | None
    student_id: int
    technician_id: int | None
    category_id: int
    description: str
    status: str = "Nuevo"
    priority: str | None = None
    before_photo_id: int
    after_photo_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    location: IncidentLocation | None = None

    def __post_init__(self) -> None:
        if not self.description or not self.description.strip():
            raise ValueError("La descripción del incidente no puede estar vacía")

        if not self.student_id:
            raise ValueError("El incidente debe tener un estudiante asociado")

        if not self.category_id:
            raise ValueError("El incidente debe tener una categoría asociada")

        if not self.before_photo_id:
            raise ValueError("El incidente debe tener una foto 'antes'")
