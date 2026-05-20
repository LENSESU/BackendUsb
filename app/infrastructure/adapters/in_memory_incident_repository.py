"""Adaptador in-memory para Incidentes (desarrollo y tests).

Creado para #107/#108/#109 (HU-E2-011).
Sigue el mismo patrón que ``InMemoryItemRepository``.
"""

from datetime import datetime
from uuid import UUID

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.domain.entities.incident import Incident


class InMemoryIncidentRepository(IncidentRepositoryPort):
    """Almacén en memoria — útil para tests sin base de datos.

    Implementa ``IncidentRepositoryPort`` usando un diccionario Python.
    Se usa en la suite de pruebas (#109) y durante desarrollo local.
    Los datos se pierden al reiniciar el proceso.
    """

    def __init__(self) -> None:
        # dict[UUID → Incident] indexado por ID del incidente
        self._store: dict[UUID, Incident] = {}

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Busca un incidente en el diccionario por UUID."""
        return self._store.get(incident_id)

    def list_all(
        self,
        *,
        status: str | None = None,
        category_id: UUID | None = None,
        priority: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Incident]:
        """Retorna incidentes con filtros opcionales."""
        results = list(self._store.values())
        if status is not None:
            results = [i for i in results if i.status == status]
        if category_id is not None:
            results = [i for i in results if i.category_id == category_id]
        if priority is not None:
            results = [i for i in results if i.priority == priority]
        if date_from is not None:
            results = [i for i in results if i.created_at is not None and i.created_at >= date_from]
        if date_to is not None:
            results = [i for i in results if i.created_at is not None and i.created_at <= date_to]
        return results

    def save(self, incident: Incident) -> Incident:
        """Guarda o sobrescribe un incidente por su ID."""
        self._store[incident.id] = incident
        return incident

    def delete(self, incident_id: UUID) -> bool:
        """Elimina un incidente por ID. Retorna True si existía."""
        return self._store.pop(incident_id, None) is not None
