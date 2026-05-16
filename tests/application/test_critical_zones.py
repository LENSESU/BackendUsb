"""Tests para la lógica de zonas críticas (HU-E6-043 tarea #273)."""

from uuid import uuid4

import pytest

from app.application.services.incident_service import IncidentService
from app.domain.entities.incident import Incident, IncidentLocation, IncidentPriority
from tests.application.test_incident_service_creation import InMemoryIncidentRepository


def _make_incident(
    campus_place: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    priority: str = IncidentPriority.MEDIA,
) -> Incident:
    return Incident(
        id=uuid4(),
        student_id=uuid4(),
        technician_id=None,
        category_id=uuid4(),
        description="Test",
        status="Nuevo",
        priority=priority,
        location=IncidentLocation(
            campus_place=campus_place,
            latitude=latitude,
            longitude=longitude,
        ),
    )


def test_agrupa_por_campus_place() -> None:
    repo = InMemoryIncidentRepository()
    repo.save(_make_incident(campus_place="Biblioteca"))
    repo.save(_make_incident(campus_place="Biblioteca"))
    repo.save(_make_incident(campus_place="Lago"))
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    names = [z["zone"] for z in zones]

    assert len(zones) == 2
    assert "Biblioteca" in names
    assert "Lago" in names


def test_score_ponderado_por_prioridad() -> None:
    repo = InMemoryIncidentRepository()
    repo.save(_make_incident(campus_place="Central", priority=IncidentPriority.ALTA))
    repo.save(_make_incident(campus_place="Central", priority=IncidentPriority.MEDIA))
    repo.save(_make_incident(campus_place="Central", priority=IncidentPriority.BAJA))
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    assert zones[0]["score"] == 6  # 3 + 2 + 1


def test_criticidad_alta() -> None:
    repo = InMemoryIncidentRepository()
    for _ in range(3):
        repo.save(_make_incident(campus_place="Cancha", priority=IncidentPriority.ALTA))
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    assert zones[0]["criticality"] == "Alta"  # score=9


def test_criticidad_media() -> None:
    repo = InMemoryIncidentRepository()
    repo.save(_make_incident(campus_place="Naranjos", priority=IncidentPriority.ALTA))
    repo.save(_make_incident(campus_place="Naranjos", priority=IncidentPriority.MEDIA))
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    assert zones[0]["criticality"] == "Media"  # score=5


def test_criticidad_baja() -> None:
    repo = InMemoryIncidentRepository()
    repo.save(_make_incident(campus_place="Cedro", priority=IncidentPriority.BAJA))
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    assert zones[0]["criticality"] == "Baja"  # score=1


def test_ordenado_por_score_descendente() -> None:
    repo = InMemoryIncidentRepository()
    repo.save(_make_incident(campus_place="Lago", priority=IncidentPriority.BAJA))
    repo.save(_make_incident(campus_place="Central", priority=IncidentPriority.ALTA))
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    assert zones[0]["zone"] == "Central"


def test_ignora_incidentes_sin_ubicacion() -> None:
    repo = InMemoryIncidentRepository()
    inc = Incident(
        id=uuid4(),
        student_id=uuid4(),
        technician_id=None,
        category_id=uuid4(),
        description="Sin ubicación",
        status="Nuevo",
        priority=IncidentPriority.ALTA,
        location=None,
    )
    repo.save(inc)
    service = IncidentService(repository=repo)

    zones = service.get_critical_zones()
    assert zones == []