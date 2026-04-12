"""Entidad de dominio: Incident."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID


class IncidentStatus(str, Enum):
    """Estados posibles de un incidente."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class IncidentPriority(str, Enum):
    """Niveles de prioridad de un incidente."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentCategory(str, Enum):
    """Categorías de un incidente."""

    HARDWARE = "hardware"
    SOFTWARE = "software"
    NETWORK = "network"
    SECURITY = "security"
    OTHER = "other"


@dataclass
class Incident:
    """Entidad de negocio Incident. Sin dependencias de frameworks."""

    id: UUID
    title: str
    reported_by: str
    status: IncidentStatus = IncidentStatus.OPEN
    priority: IncidentPriority = IncidentPriority.MEDIUM
    category: IncidentCategory = IncidentCategory.OTHER
    description: str | None = None
    location: str | None = None
    assigned_to: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("El título no puede estar vacío")
        if not self.reported_by or not self.reported_by.strip():
            raise ValueError("El campo reported_by no puede estar vacío")
