"""Rutas HTTP para gestión y consulta de técnicos."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from passlib.context import CryptContext

from app.api.dependencies.auth import require_role
from app.api.dependencies.technician import get_technician_service
from app.api.schemas.technician import (
    AvailableTechnicianResponse,
    TechnicianAdminResponse,
    TechnicianCreateRequest,
    TechnicianIncidentsResponse,
    TechnicianIncidentSummary,
    TechnicianUpdateRequest,
)
from app.application.services.technician_service import TechnicianService
from app.domain.entities.incident import Incident
from app.domain.entities.user import User

router = APIRouter()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Helpers de mapeo
# ---------------------------------------------------------------------------


def _to_available(user: User) -> AvailableTechnicianResponse:
    assert user.id is not None
    return AvailableTechnicianResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
    )


def _to_admin(user: User) -> TechnicianAdminResponse:
    assert user.id is not None
    return TechnicianAdminResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def _incident_to_summary(incident: Incident) -> TechnicianIncidentSummary:
    assert incident.id is not None
    return TechnicianIncidentSummary(
        id=incident.id,
        description=incident.description,
        status=incident.status.value,
        priority=incident.priority,
        campus_place=incident.location.campus_place if incident.location else None,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/available",
    response_model=list[AvailableTechnicianResponse],
    summary="Técnicos disponibles para asignación",
    dependencies=[Depends(require_role("Administrator", "Technician"))],
)
def list_available_technicians(
    technician_service: TechnicianService = Depends(get_technician_service),
) -> list[AvailableTechnicianResponse]:
    """Lista técnicos activos sin incidentes abiertos asignados."""
    users = technician_service.list_available_technicians()
    return [_to_available(u) for u in users]


@router.get(
    "/{technician_id}",
    response_model=TechnicianAdminResponse,
    summary="Detalle de un técnico",
    dependencies=[Depends(require_role("Administrator", "Technician"))],
)
def get_technician_by_id(
    technician_id: UUID,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> TechnicianAdminResponse:
    """Retorna los datos de un técnico por su ID (incluye estado activo/inactivo)."""
    user = technician_service.get_technician_by_id(technician_id)
    return _to_admin(user)


# ---------------------------------------------------------------------------
# Endpoints — solo Administrator
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[TechnicianAdminResponse],
    summary="Listar todos los técnicos",
    dependencies=[Depends(require_role("Administrator"))],
)
def list_all_technicians(
    technician_service: TechnicianService = Depends(get_technician_service),
) -> list[TechnicianAdminResponse]:
    """
    Lista todos los técnicos registrados, activos e inactivos.
    Solo accesible para administradores.
    """
    users = technician_service.list_all_technicians()
    return [_to_admin(u) for u in users]


@router.post(
    "",
    response_model=TechnicianAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo técnico",
    dependencies=[Depends(require_role("Administrator"))],
)
def create_technician(
    body: TechnicianCreateRequest,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> TechnicianAdminResponse:
    """
    Registra un nuevo técnico en el sistema.
    La contraseña se almacena con hash bcrypt.
    Retorna 409 si el email ya está registrado.
    """
    password_hash = _pwd_context.hash(body.password)
    user = technician_service.register_technician(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        password_hash=password_hash,
    )
    return _to_admin(user)


@router.patch(
    "/{technician_id}",
    response_model=TechnicianAdminResponse,
    summary="Actualizar datos de un técnico",
    dependencies=[Depends(require_role("Administrator"))],
)
def update_technician(
    technician_id: UUID,
    body: TechnicianUpdateRequest,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> TechnicianAdminResponse:
    """
    Actualiza nombre, apellido y/o email de un técnico.
    Solo se modifican los campos presentes en el body.
    Retorna 409 si el nuevo email ya pertenece a otro usuario.
    """
    user = technician_service.update_technician(
        technician_id=technician_id,
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
    )
    return _to_admin(user)


@router.patch(
    "/{technician_id}/deactivate",
    response_model=TechnicianAdminResponse,
    summary="Desactivar técnico",
    dependencies=[Depends(require_role("Administrator"))],
)
def deactivate_technician(
    technician_id: UUID,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> TechnicianAdminResponse:
    """
    Desactiva un técnico (is_active = False).
    Un técnico inactivo no puede ser asignado a nuevos incidentes.
    Retorna 409 si ya estaba inactivo.
    """
    user = technician_service.deactivate_technician(technician_id)
    return _to_admin(user)


@router.patch(
    "/{technician_id}/activate",
    response_model=TechnicianAdminResponse,
    summary="Reactivar técnico",
    dependencies=[Depends(require_role("Administrator"))],
)
def activate_technician(
    technician_id: UUID,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> TechnicianAdminResponse:
    """
    Reactiva un técnico previamente desactivado (is_active = True).
    Retorna 409 si ya estaba activo.
    """
    user = technician_service.activate_technician(technician_id)
    return _to_admin(user)


@router.get(
    "/{technician_id}/incidents",
    response_model=TechnicianIncidentsResponse,
    summary="Incidentes asignados a un técnico",
    dependencies=[Depends(require_role("Administrator"))],
)
def get_technician_incidents(
    technician_id: UUID,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> TechnicianIncidentsResponse:
    """
    Retorna el técnico y todos sus incidentes asignados (histórico completo),
    ordenados del más reciente al más antiguo.
    """
    technician, incidents = technician_service.get_technician_incidents(technician_id)
    return TechnicianIncidentsResponse(
        technician=_to_admin(technician),
        incidents=[_incident_to_summary(i) for i in incidents],
        total=len(incidents),
    )
