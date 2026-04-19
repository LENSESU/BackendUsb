"""Rutas HTTP para consulta de técnicos."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_role
from app.api.dependencies.technician import get_technician_service
from app.api.schemas.technician import AvailableTechnicianResponse
from app.application.services.technician_service import TechnicianService
from app.domain.entities.user import User

router = APIRouter()


def _user_to_available_response(user: User) -> AvailableTechnicianResponse:
    """Convierte entidad User a DTO sin exponer hash ni rol."""
    assert user.id is not None
    return AvailableTechnicianResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
    )


@router.get(
    "/available",
    response_model=list[AvailableTechnicianResponse],
    dependencies=[
        Depends(require_role("Administrator", "Technician")),
    ],
)
def list_available_technicians(
    technician_service: TechnicianService = Depends(get_technician_service),
) -> list[AvailableTechnicianResponse]:
    """Lista técnicos activos disponibles (sin incidentes abiertos asignados)."""
    users = technician_service.list_available_technicians()
    return [_user_to_available_response(u) for u in users]


@router.get(
    "/{technician_id}",
    response_model=AvailableTechnicianResponse,
    dependencies=[
        Depends(require_role("Administrator", "Technician")),
    ],
)
def get_technician_by_id(
    technician_id: UUID,
    technician_service: TechnicianService = Depends(get_technician_service),
) -> AvailableTechnicianResponse:
    """Retorna los datos públicos de un técnico por su ID."""
    user = technician_service.get_technician_by_id(technician_id)
    return _user_to_available_response(user)