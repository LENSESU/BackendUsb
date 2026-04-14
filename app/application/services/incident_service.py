"""Caso de uso: operaciones sobre Incidentes."""

from uuid import UUID, uuid4

from fastapi import HTTPException

from app.application.ports import IncidentRepositoryPort
from app.application.ports.incident_category_repository import (
    IncidentCategoryRepositoryPort,
)
from app.domain.entities.incident import (
    Incident,
    IncidentLocation,
    IncidentStatus,
    incident_status_as_str,
    is_known_incident_status,
    validate_incident_status_transition,
)


class IncidentService:
    """Servicio de aplicación para Incidentes. Orquesta dominio y puertos."""

    def __init__(
        self,
        repository: IncidentRepositoryPort,
        category_repository: IncidentCategoryRepositoryPort | None = None,
    ) -> None:
        self._repository = repository
        self._category_repository = category_repository

    def get_incident(self, incident_id: UUID) -> Incident | None:
        return self._repository.get_by_id(incident_id)

    def list_incidents(self) -> list[Incident]:
        return self._repository.list_all()

    def get_recent_incidents(
        self,
        user_id: UUID,
        limit: int = 5,
        role_name: str = "Student",
    ) -> list[Incident]:
        """Retorna incidentes recientes visibles para el usuario autenticado."""
        incidents = self._repository.list_all()
        if role_name == "Administrator":
            visible_incidents = incidents
        elif role_name == "Technician":
            visible_incidents = [i for i in incidents if i.technician_id == user_id]
        else:
            visible_incidents = [i for i in incidents if i.student_id == user_id]
        return visible_incidents[:limit]

    def create_incident(
        self,
        student_id: UUID,
        category_id: UUID,
        description: str,
        before_photo_id: UUID | None = None,
        technician_id: UUID | None = None,
        campus_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        priority: str | None = None,
        status: str | None = None,
    ) -> Incident:

        if self._category_repository is not None:
            category = self._category_repository.find_by_id(str(category_id))
            if category is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"La categoría con id '{category_id}' no existe.",
                )

        location = None
        if campus_place is not None or latitude is not None or longitude is not None:
            location = IncidentLocation(
                campus_place=campus_place,
                latitude=latitude,
                longitude=longitude,
            )

        if status is None or not str(incident_status_as_str(status)).strip():
            resolved_status = IncidentStatus.NUEVO.value
        else:
            candidate = incident_status_as_str(status)
            if not is_known_incident_status(candidate):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": (
                            f"Estado de incidente no válido: {candidate!r}. "
                            f"Valores permitidos: "
                            f"{', '.join(s.value for s in IncidentStatus)}."
                        ),
                        "error_code": "INCIDENT_STATUS_INVALID",
                    },
                )
            if candidate != IncidentStatus.NUEVO.value:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "message": (
                            "Al crear un incidente solo se permite el estado "
                            f"inicial {IncidentStatus.NUEVO.value!r}."
                        ),
                        "error_code": "INCIDENT_STATUS_CREATE_INVALID",
                    },
                )
            resolved_status = candidate

        incident = Incident(
            id=uuid4(),
            student_id=student_id,
            technician_id=technician_id,
            category_id=category_id,
            description=description.strip(),
            status=resolved_status,
            priority=priority,
            before_photo_id=before_photo_id,
            after_photo_id=None,
            created_at=None,
            updated_at=None,
            location=location,
        )
        return self._repository.save(incident)

    def update_incident(
        self,
        incident_id: UUID,
        *,
        technician_id: UUID | None = None,
        category_id: UUID | None = None,
        description: str | None = None,
        campus_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        status: str | None = None,
        priority: str | None = None,
        before_photo_id: UUID | None = None,
        after_photo_id: UUID | None = None,
    ) -> Incident | None:
        existing = self._repository.get_by_id(incident_id)
        if existing is None:
            return None
        if category_id is not None and self._category_repository is not None:
            category = self._category_repository.find_by_id(str(category_id))
            if category is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"La categoría con id '{category_id}' no existe.",
                )
        loc = existing.location
        if campus_place is not None or latitude is not None or longitude is not None:
            location = IncidentLocation(
                campus_place=(
                    campus_place
                    if campus_place is not None
                    else (loc.campus_place if loc else None)
                ),
                latitude=(
                    latitude
                    if latitude is not None
                    else (loc.latitude if loc else None)
                ),
                longitude=(
                    longitude
                    if longitude is not None
                    else (loc.longitude if loc else None)
                ),
            )
        else:
            location = existing.location
        tech_id = technician_id if technician_id is not None else existing.technician_id
        cat_id = category_id if category_id is not None else existing.category_id
        before_id = (
            before_photo_id if before_photo_id is not None else existing.before_photo_id
        )
        after_id = (
            after_photo_id if after_photo_id is not None else existing.after_photo_id
        )
        resolved_status = existing.status
        if status is not None:
            new_status_str = incident_status_as_str(status)
            if new_status_str != existing.status:
                try:
                    validate_incident_status_transition(existing.status, new_status_str)
                except ValueError as e:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "message": str(e),
                            "error_code": "INCIDENT_STATUS_TRANSITION_INVALID",
                        },
                    ) from e
            resolved_status = new_status_str
        updated = Incident(
            id=existing.id,
            student_id=existing.student_id,
            technician_id=tech_id,
            category_id=cat_id,
            description=(description or existing.description).strip(),
            status=resolved_status,
            priority=priority if priority is not None else existing.priority,
            before_photo_id=before_id,
            after_photo_id=after_id,
            created_at=existing.created_at,
            updated_at=None,
            location=location,
        )
        return self._repository.save(updated)

    def delete_incident(self, incident_id: UUID) -> bool:
        return self._repository.delete(incident_id)
