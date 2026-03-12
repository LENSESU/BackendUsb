"""Tests #116 — Consulta y validación de categorías en incidentes."""
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.application.services.incident_service import IncidentService
from app.domain.entities.incident_category import IncidentCategory


def make_service(category_exists: bool) -> IncidentService:
    category_repo = MagicMock()
    incident_repo = MagicMock()

    if category_exists:
        fake_category = IncidentCategory(
            id=UUID("16edf08c-acf2-427d-94a9-9492c764a552"),
            name="Infraestructura",
        )
        category_repo.find_by_id.return_value = fake_category
    else:
        category_repo.find_by_id.return_value = None

    fake_incident = MagicMock()
    fake_incident.id = uuid4()
    incident_repo.save.return_value = fake_incident

    return IncidentService(repository=incident_repo, category_repository=category_repo)


def test_category_invalida_lanza_error():
    service = make_service(category_exists=False)
    with pytest.raises(HTTPException) as exc_info:
        service.create_incident(
            student_id=uuid4(),
            category_id=UUID("00000000-0000-0000-0000-000000000000"),
            description="Test",
        )
    assert exc_info.value.status_code == 422


def test_category_invalida_mensaje_claro():
    bad_id = UUID("00000000-0000-0000-0000-000000000000")
    service = make_service(category_exists=False)
    with pytest.raises(HTTPException) as exc_info:
        service.create_incident(
            student_id=uuid4(),
            category_id=bad_id,
            description="Test",
        )
    assert str(bad_id) in exc_info.value.detail


def test_category_valida_llama_save():
    service = make_service(category_exists=True)
    valid_id = UUID("16edf08c-acf2-427d-94a9-9492c764a552")
    service.create_incident(
        student_id=uuid4(),
        category_id=valid_id,
        description="Gotera en aula 301",
    )
    service._repository.save.assert_called_once()


def test_category_valida_mapea_category_id():
    service = make_service(category_exists=True)
    valid_id = UUID("16edf08c-acf2-427d-94a9-9492c764a552")
    service.create_incident(
        student_id=uuid4(),
        category_id=valid_id,
        description="Gotera en aula 301",
    )
    incident_guardado = service._repository.save.call_args[0][0]
    assert incident_guardado.category_id == valid_id