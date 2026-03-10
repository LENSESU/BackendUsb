"""Caso de uso: operaciones sobre Incidentes. Depende del puerto, no de implementaciones."""

from uuid import UUID, uuid4

from app.application.ports import IncidentRepositoryPort
from app.domain.entities.incident import Incident, IncidentLocation


class IncidentService:
    """Servicio de aplicación para Incidentes. Orquesta dominio y puertos."""

    def __init__(self, repository: IncidentRepositoryPort) -> None:
        self._repository = repository

    def get_incident(self, incident_id: UUID) -> Incident | None:
        return self._repository.get_by_id(incident_id)

    def list_incidents(self) -> list[Incident]:
        return self._repository.list_all()

    def     create_incident(
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
        location = None
        if campus_place is not None or latitude is not None or longitude is not None:
            location = IncidentLocation(
                campus_place=campus_place,
                latitude=latitude,
                longitude=longitude,
            )
        incident = Incident(
            id=uuid4(),
            student_id=student_id,
            technician_id=technician_id,
            category_id=category_id,
            description=description.strip(),
            status=status if status else "Nuevo",
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
        loc = existing.location
        if (
            campus_place is not None
            or latitude is not None
            or longitude is not None
        ):
            location = IncidentLocation(
                campus_place=(
                    campus_place if campus_place is not None
                    else (loc.campus_place if loc else None)
                ),
                latitude=(
                    latitude if latitude is not None
                    else (loc.latitude if loc else None)
                ),
                longitude=(
                    longitude if longitude is not None
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
        updated = Incident(
            id=existing.id,
            student_id=existing.student_id,
            technician_id=tech_id,
            category_id=cat_id,
            description=(description or existing.description).strip(),
            status=status if status is not None else existing.status,
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
