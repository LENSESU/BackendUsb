"""Servicio de asignación y consulta de técnicos."""

from uuid import UUID

from fastapi import HTTPException, status

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.ports.technician_repository import TechnicianRepositoryPort
from app.domain.entities.incident import Incident
from app.domain.entities.user import User


class TechnicianService:
    """Orquesta validación de incidente/técnico y consultas de disponibilidad."""

    def __init__(
        self,
        technician_repository: TechnicianRepositoryPort,
        incident_repository: IncidentRepositoryPort,
    ) -> None:
        self._technicians = technician_repository
        self._incidents = incident_repository

    def list_available_technicians(self) -> list[User]:
        """Retorna técnicos activos sin carga en incidentes Nuevo o En_proceso."""
        return self._technicians.technician_available_list_all()

    def assign_technician_to_incident(
        self,
        incident_id: UUID,
        technician_id: UUID,
    ) -> Incident:
        """
        Asocia un técnico activo con rol adecuado a un incidente existente.

        Raises:
            HTTPException 404: Incidente inexistente o técnico no válido/inactivo.
        """
        assigned = self._technicians.assign_technician_to_incident(
            str(technician_id), str(incident_id)
        )
        if assigned is not None:
            updated = self._incidents.get_by_id(incident_id)
            if updated is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "Incidente no encontrado",
                        "error_code": "INCIDENT_NOT_FOUND",
                    },
                )
            return updated

        if self._incidents.get_by_id(incident_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Incidente no encontrado",
                    "error_code": "INCIDENT_NOT_FOUND",
                },
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": (
                    "El técnico no existe, no tiene rol de técnico o está inactivo"
                ),
                "error_code": "TECHNICIAN_NOT_ASSIGNABLE",
            },
        )
