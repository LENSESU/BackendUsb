"""Tests de aplicación para IncidentService.create_incident.

Estos tests validan que el servicio de incidentes:
- Crea un incidente mínimo con los campos requeridos.
- Limpia espacios en la descripción.
- Asigna el estado por defecto cuando no se especifica.
"""

from uuid import UUID, uuid4

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_service import IncidentService
from app.domain.entities.incident import Incident


class InMemoryIncidentRepository(IncidentRepositoryPort):
    """Repositorio de incidentes en memoria para pruebas de IncidentService.

    Propósito:
        Implementar el puerto IncidentRepositoryPort en memoria para verificar
        el comportamiento de IncidentService sin depender de una base de datos real.

    Atributos:
        _store:
            Diccionario interno que mapea IDs de incidente a entidades Incident.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, Incident] = {}

    def get_by_id(self, incident_id: UUID) -> Incident | None:
        """Obtiene un incidente por su ID desde el almacén en memoria."""
        return self._store.get(incident_id)

    def list_all(self) -> list[Incident]:
        """Devuelve todos los incidentes almacenados en memoria."""
        return list(self._store.values())

    def save(self, incident: Incident) -> Incident:
        """Guarda o actualiza un incidente en el almacén en memoria."""
        assert incident.id is not None
        self._store[incident.id] = incident
        return incident

    def delete(self, incident_id: UUID) -> bool:
        """Elimina un incidente por su ID. Retorna True si existía."""
        return self._store.pop(incident_id, None) is not None


def test_create_incident_minimal_fields() -> None:
    """Crea un incidente mínimo y verifica que se persiste correctamente.

    Escenario:
        Simula la creación de un incidente con los mismos campos mínimos que
        utilizaba el script `create_incident_for_evidence`, pero como prueba
        automatizada de servicios.

    Validaciones:
        - Se genera un ID de incidente.
        - Se respeta el student_id y category_id de entrada.
        - La descripción se guarda sin espacios extra.
        - El estado por defecto es "Nuevo".
        - El incidente queda almacenado en el repositorio.
    """
    repo = InMemoryIncidentRepository()
    service = IncidentService(repository=repo)

    student_id = uuid4()
    category_id = uuid4()

    incident = service.create_incident(
        student_id=student_id,
        category_id=category_id,
        description="  Incidente de prueba para carga de evidencia  ",
    )

    assert incident.id is not None
    assert incident.student_id == student_id
    assert incident.category_id == category_id
    assert incident.description == "Incidente de prueba para carga de evidencia"
    assert incident.status == "Nuevo"
    assert incident.before_photo_id is None
    assert incident.after_photo_id is None

    stored = repo.get_by_id(incident.id)
    assert stored is not None
    assert stored.id == incident.id

