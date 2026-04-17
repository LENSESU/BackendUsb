"""Pruebas del flujo de estados de incidentes (transiciones válidas)."""

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.application.services.incident_service import IncidentService
from app.domain.entities.incident import (
    IncidentStatus,
    validate_incident_status_transition,
)
from tests.application.test_incident_service_creation import InMemoryIncidentRepository


def test_domain_allows_nuevo_to_en_proceso() -> None:
    validate_incident_status_transition(
        IncidentStatus.NUEVO.value, IncidentStatus.EN_PROCESO.value
    )


def test_domain_allows_en_proceso_to_resuelto() -> None:
    validate_incident_status_transition(
        IncidentStatus.EN_PROCESO.value, IncidentStatus.RESUELTO.value
    )


def test_domain_same_status_is_noop() -> None:
    validate_incident_status_transition(
        IncidentStatus.EN_PROCESO.value, IncidentStatus.EN_PROCESO.value
    )


def test_domain_rejects_skip_to_resuelto() -> None:
    with pytest.raises(ValueError, match="Transición de estado no permitida"):
        validate_incident_status_transition(
            IncidentStatus.NUEVO.value, IncidentStatus.RESUELTO.value
        )


def test_domain_rejects_backwards() -> None:
    with pytest.raises(ValueError, match="Transición de estado no permitida"):
        validate_incident_status_transition(
            IncidentStatus.EN_PROCESO.value, IncidentStatus.NUEVO.value
        )


def test_domain_rejects_from_resuelto() -> None:
    with pytest.raises(ValueError, match="estado final"):
        validate_incident_status_transition(
            IncidentStatus.RESUELTO.value, IncidentStatus.EN_PROCESO.value
        )


def test_domain_rejects_unknown_target_status() -> None:
    with pytest.raises(ValueError, match="no válido"):
        validate_incident_status_transition(
            IncidentStatus.NUEVO.value, "Cancelado",
        )


def test_service_update_happy_path() -> None:
    repo = InMemoryIncidentRepository()
    service = IncidentService(repository=repo)
    inc = service.create_incident(
        student_id=uuid4(),
        category_id=uuid4(),
        description="Test",
    )
    assert inc.id is not None
    updated = service.update_incident(
        inc.id, status=IncidentStatus.EN_PROCESO.value
    )
    assert updated is not None
    assert updated.status == IncidentStatus.EN_PROCESO.value
    final = service.update_incident(inc.id, status=IncidentStatus.RESUELTO.value)
    assert final is not None
    assert final.status == IncidentStatus.RESUELTO.value


def test_service_update_invalid_transition_422() -> None:
    repo = InMemoryIncidentRepository()
    service = IncidentService(repository=repo)
    inc = service.create_incident(
        student_id=uuid4(),
        category_id=uuid4(),
        description="Test",
    )
    assert inc.id is not None
    with pytest.raises(HTTPException) as ei:
        service.update_incident(inc.id, status=IncidentStatus.RESUELTO.value)
    assert ei.value.status_code == 422
    assert isinstance(ei.value.detail, dict)
    assert ei.value.detail.get("error_code") == "INCIDENT_STATUS_TRANSITION_INVALID"


def test_service_create_only_nuevo_status() -> None:
    repo = InMemoryIncidentRepository()
    service = IncidentService(repository=repo)
    sid = uuid4()
    cid = uuid4()
    with pytest.raises(HTTPException) as ei:
        service.create_incident(
            student_id=sid,
            category_id=cid,
            description="X",
            status=IncidentStatus.EN_PROCESO.value,
        )
    assert ei.value.status_code == 422
    assert ei.value.detail["error_code"] == "INCIDENT_STATUS_CREATE_INVALID"
