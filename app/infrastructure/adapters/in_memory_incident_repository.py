"""Adaptador in-memory para Incidentes (desarrollo y tests).

Creado para #107/#108/#109 (HU-E2-011).
Sigue el mismo patrón que ``InMemoryItemRepository``.
"""

from dataclasses import replace
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

    def list_all(self) -> list[Incident]:
        """Retorna todos los incidentes almacenados."""
        return list(self._store.values())

    def save(self, incident: Incident) -> Incident:
        """Guarda o sobrescribe un incidente por su ID."""
        self._store[incident.id] = incident
        return incident

    def delete(self, incident_id: UUID) -> bool:
        """Elimina un incidente por ID. Retorna True si existía."""
        return self._store.pop(incident_id, None) is not None

    def update_status(self, incident_id: UUID, new_status: str) -> Incident | None:
        """Actualiza únicamente el estado del incidente en memoria."""
        incident = self._store.get(incident_id)
        if incident is None:
            return None
        
        updated = replace(incident, status=new_status)
        self._store[incident_id] = updated
        return updated