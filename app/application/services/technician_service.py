"""Servicio de asignación, consulta y gestión de técnicos."""

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

    def get_technician_by_id(self, technician_id: UUID) -> User:
        """
        Retorna un técnico por su ID.

        Raises:
            HTTPException 404: Si el técnico no existe o no tiene rol de técnico.
        """
        technician = self._technicians.find_by_id(str(technician_id))
        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Técnico no encontrado",
                    "error_code": "TECHNICIAN_NOT_FOUND",
                },
            )
        return technician

    def assign_technician_to_incident(
        self,
        incident_id: UUID,
        technician_id: UUID,
        assigned_by_admin_id: UUID | None = None,
    ) -> Incident:
        """
        Asocia un técnico activo con rol adecuado a un incidente existente.

        Raises:
            HTTPException 404: Incidente inexistente o técnico no válido/inactivo.
        """
        assigned = self._technicians.assign_technician_to_incident(
            str(technician_id),
            str(incident_id),
            str(assigned_by_admin_id) if assigned_by_admin_id else None,
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

    # ------------------------------------------------------------------
    # Nuevos métodos — gestión admin
    # ------------------------------------------------------------------

    def list_all_technicians(self) -> list[User]:
        """Retorna todos los técnicos (activos e inactivos)."""
        return self._technicians.find_all()

    def register_technician(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
    ) -> User:
        """
        Registra un nuevo técnico en el sistema.

        Raises:
            HTTPException 409: Si el email ya está registrado.
        """
        try:
            return self._technicians.create_technician(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": str(exc),
                    "error_code": "EMAIL_ALREADY_EXISTS",
                },
            ) from exc

    def update_technician(
        self,
        technician_id: UUID,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> User:
        """
        Actualiza datos de un técnico (PATCH semántico).

        Raises:
            HTTPException 404: Si el técnico no existe.
            HTTPException 409: Si el nuevo email ya pertenece a otro usuario.
        """
        try:
            updated = self._technicians.update_technician(
                user_id=str(technician_id),
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": str(exc),
                    "error_code": "EMAIL_ALREADY_EXISTS",
                },
            ) from exc

        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Técnico no encontrado",
                    "error_code": "TECHNICIAN_NOT_FOUND",
                },
            )
        return updated

    def deactivate_technician(self, technician_id: UUID) -> User:
        """
        Desactiva un técnico.

        Raises:
            HTTPException 404: Si el técnico no existe.
            HTTPException 409: Si el técnico ya está inactivo.
        """
        technician = self._technicians.find_by_id(str(technician_id))
        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Técnico no encontrado",
                    "error_code": "TECHNICIAN_NOT_FOUND",
                },
            )
        if not technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "El técnico ya se encuentra inactivo",
                    "error_code": "TECHNICIAN_ALREADY_INACTIVE",
                },
            )
        result = self._technicians.set_active_status(str(technician_id), False)
        assert result is not None  # Garantizado: acaba de existir
        return result

    def activate_technician(self, technician_id: UUID) -> User:
        """
        Reactiva un técnico previamente desactivado.

        Raises:
            HTTPException 404: Si el técnico no existe.
            HTTPException 409: Si el técnico ya está activo.
        """
        technician = self._technicians.find_by_id(str(technician_id))
        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Técnico no encontrado",
                    "error_code": "TECHNICIAN_NOT_FOUND",
                },
            )
        if technician.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "El técnico ya se encuentra activo",
                    "error_code": "TECHNICIAN_ALREADY_ACTIVE",
                },
            )
        result = self._technicians.set_active_status(str(technician_id), True)
        assert result is not None
        return result

    def get_technician_incidents(
        self, technician_id: UUID
    ) -> tuple[User, list[Incident]]:
        """
        Retorna el técnico y la lista de todos sus incidentes asignados.

        Raises:
            HTTPException 404: Si el técnico no existe.
        """
        technician = self._technicians.find_by_id(str(technician_id))
        if technician is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Técnico no encontrado",
                    "error_code": "TECHNICIAN_NOT_FOUND",
                },
            )
        incidents = self._technicians.find_incidents_by_technician(str(technician_id))
        return technician, incidents
