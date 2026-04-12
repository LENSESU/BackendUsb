"""Adaptador en memoria que implementa IncidentRepositoryPort.
Se puede sustituir por SQL, NoSQL, etc."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.ports import IncidentRepositoryPort
from app.domain.entities import Incident
from app.domain.entities.incident import IncidentCategory, IncidentPriority, IncidentStatus


def _seed_incidents() -> dict[UUID, Incident]:
    """Genera incidentes de ejemplo para desarrollo y pruebas manuales."""
    samples = [
        Incident(
            id=uuid4(),
            title="Fallo en el servidor de base de datos",
            description="El servidor PostgreSQL dejó de responder tras un pico de carga.",
            category=IncidentCategory.NETWORK,
            status=IncidentStatus.IN_PROGRESS,
            priority=IncidentPriority.CRITICAL,
            location="Sala de servidores — Piso 2",
            reported_by="ana.garcia@empresa.com",
            assigned_to="ops-team",
            created_at=datetime(2026, 4, 10, 9, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 10, 10, 15, tzinfo=timezone.utc),
        ),
        Incident(
            id=uuid4(),
            title="Pantalla de login en blanco en Chrome",
            description="Usuarios con Chrome 124 no pueden iniciar sesión.",
            category=IncidentCategory.SOFTWARE,
            status=IncidentStatus.OPEN,
            priority=IncidentPriority.HIGH,
            location="Oficina central",
            reported_by="pedro.lopez@empresa.com",
            created_at=datetime(2026, 4, 11, 8, 30, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 11, 8, 30, tzinfo=timezone.utc),
        ),
        Incident(
            id=uuid4(),
            title="Exportación de reportes lenta",
            description="El módulo de reportes tarda más de 2 minutos en exportar a Excel.",
            category=IncidentCategory.SOFTWARE,
            status=IncidentStatus.OPEN,
            priority=IncidentPriority.MEDIUM,
            location=None,
            reported_by="maria.torres@empresa.com",
            created_at=datetime(2026, 4, 12, 7, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 12, 7, 0, tzinfo=timezone.utc),
        ),
        Incident(
            id=uuid4(),
            title="Error 500 al eliminar usuario",
            description=None,
            category=IncidentCategory.SOFTWARE,
            status=IncidentStatus.RESOLVED,
            priority=IncidentPriority.LOW,
            location="Remoto",
            reported_by="luis.ramirez@empresa.com",
            assigned_to="dev-team",
            created_at=datetime(2026, 4, 9, 14, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 4, 11, 16, 45, tzinfo=timezone.utc),
        ),
    ]
    return {i.id: i for i in samples}


class InMemoryIncidentRepository(IncidentRepositoryPort):
    """Implementación del puerto de Incidents usando un diccionario en memoria."""

    def __init__(self) -> None:
        self._storage: dict[UUID, Incident] = _seed_incidents()

    def list_all(self) -> list[Incident]:
        return list(self._storage.values())

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        return self._storage.get(incident_id)

    def save(self, incident: Incident) -> Incident:
        self._storage[incident.id] = incident
        return incident
