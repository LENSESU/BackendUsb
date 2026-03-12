"""Adaptador en memoria para IncidentRepositoryPort (tests sin BD)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.domain.entities.incident import Incident


class InMemoryIncidentRepository(IncidentRepositoryPort):
    """Simula persistencia de incidentes en memoria para tests."""

    def __init__(self) -> None:
        self._incidents: dict[UUID, Incident] = {}
        self._after_photo_ids: dict[UUID, UUID] = {}

    def add(self, incident: Incident) -> None:
        """Añade un incidente para que get_by_id lo encuentre (solo tests)."""
        if incident.id is None:
            raise ValueError("El incidente debe tener id para añadirlo.")
        self._incidents[incident.id] = incident

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un incidente por ID.

        Si no está en memoria, retorna un stub para tests.
        """
        if incident_id in self._incidents:
            inc = self._incidents[incident_id]
            # Aplicar after_photo_id si se había actualizado
            after_id = self._after_photo_ids.get(incident_id)
            if after_id is not None and (
                inc.after_photo_id is None or inc.after_photo_id != after_id
            ):
                return Incident(
                    id=inc.id,
                    student_id=inc.student_id,
                    technician_id=inc.technician_id,
                    category_id=inc.category_id,
                    description=inc.description,
                    status=inc.status,
                    priority=inc.priority,
                    before_photo_id=inc.before_photo_id,
                    after_photo_id=after_id,
                    created_at=inc.created_at,
                    updated_at=inc.updated_at,
                    location=inc.location,
                )
            return inc
        # Para tests que no insertan incidentes: devolver un stub.
        # Esto permite que el flujo continúe sin una BD real.
        stub_id = uuid4()
        return Incident(
            id=incident_id,
            student_id=stub_id,
            technician_id=None,
            category_id=stub_id,
            description="Stub incident",
            status="New",
            priority=None,
            before_photo_id=stub_id,
            after_photo_id=None,
            created_at=datetime.now(UTC),
            updated_at=None,
            location=None,
        )

    def set_after_photo_id(self, incident_id: UUID, file_id: UUID) -> None:
        """Registra la asociación after_photo_id en memoria."""
        self._after_photo_ids[incident_id] = file_id
        if incident_id in self._incidents:
            inc = self._incidents[incident_id]
            self._incidents[incident_id] = Incident(
                id=inc.id,
                student_id=inc.student_id,
                technician_id=inc.technician_id,
                category_id=inc.category_id,
                description=inc.description,
                status=inc.status,
                priority=inc.priority,
                before_photo_id=inc.before_photo_id,
                after_photo_id=file_id,
                created_at=inc.created_at,
                updated_at=inc.updated_at,
                location=inc.location,
            )
