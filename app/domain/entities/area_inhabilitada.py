from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class AreaInhabilitada:
    id: UUID | None
    nombre: str
    motivo: str
    fecha_inicio: datetime
    descripcion: str | None = None
    fecha_fin: datetime | None = None
    activa: bool = True
    lugar_campus: str | None = None
    latitud: float | None = None
    longitud: float | None = None
    registrada_por_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del área no puede estar vacío.")
        if not self.motivo or not self.motivo.strip():
            raise ValueError("El motivo de inhabilitación no puede estar vacío.")
        if self.fecha_fin is not None and self.fecha_fin < self.fecha_inicio:
            raise ValueError(
                "La fecha de fin no puede ser anterior a la fecha de inicio."
            )
