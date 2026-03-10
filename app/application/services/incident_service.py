"""Caso de uso: creación de Incidentes.

Creado para #107/#108/#109 (HU-E2-011 Crear Incidente).
Sigue el mismo patrón que ``ItemService``.

#107 — El servicio se encarga de inyectar los metadatos automáticos
(``student_id``, ``created_at``) de forma que el cliente nunca los controle.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.ports.incident_repository import IncidentRepositoryPort
from app.domain.entities.incident import Incident, IncidentLocation


class IncidentService:
    """Servicio de aplicación para Incidentes.

    Orquesta la creación de incidentes aplicando las reglas de negocio
    definidas en la HU-E2-011.  Delega la persistencia al puerto
    ``IncidentRepositoryPort`` (inyección de dependencias).
    """

    def __init__(self, repository: IncidentRepositoryPort) -> None:
        """Inicializa el servicio con un repositorio concreto.

        Args:
            repository: Implementación del puerto de persistencia
                        (in-memory para tests, SQL para producción).
        """
        self._repository = repository

    def create_incident(
        self,
        *,
        student_id: UUID,
        category_id: UUID,
        description: str,
        before_photo_id: UUID,
        priority: str | None = None,
        campus_place: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> Incident:
        """Crea un incidente con metadatos automáticos.

        Metadatos controlados por el servidor (#107):
          - ``student_id``: proviene del JWT del usuario autenticado,
            **nunca** del payload del cliente.
          - ``created_at``: se fija a ``datetime.now(UTC)`` en el momento
            de la creación; el cliente no puede sobrescribirlo.
          - ``status``: se deja en el valor por defecto de la entidad
            de dominio (``"Nuevo"``); no se acepta del payload.

        Args:
            student_id:      UUID del usuario autenticado (desde JWT).
            category_id:     UUID de la categoría del incidente.
            description:     Texto descriptivo del incidente.
            before_photo_id: UUID de la foto "antes" ya subida.
            priority:        Prioridad opcional ("Alta", "Media", etc.).
            campus_place:    Lugar textual dentro del campus (opcional).
            latitude:        Coordenada latitud (opcional).
            longitude:       Coordenada longitud (opcional).

        Returns:
            Incidente creado con ID, metadatos automáticos y datos de negocio.
        """
        # [#107] Construir ubicación solo si se proporcionó algún dato
        location = None
        if campus_place or latitude is not None or longitude is not None:
            location = IncidentLocation(
                campus_place=campus_place,
                latitude=latitude,
                longitude=longitude,
            )

        # [#107] created_at se asigna aquí (hora del servidor UTC)
        # [#107] student_id viene del JWT — el servicio lo recibe ya validado
        # [#107] status="Nuevo" es el default de la entidad de dominio
        incident = Incident(
            id=uuid4(),
            student_id=student_id,
            technician_id=None,
            category_id=category_id,
            description=description.strip(),
            before_photo_id=before_photo_id,
            priority=priority,
            created_at=datetime.now(timezone.utc),
            location=location,
        )
        return self._repository.save(incident)

    def get_incident(self, incident_id: UUID) -> Incident | None:
        """Obtiene un incidente por su ID.  Retorna None si no existe."""
        return self._repository.get_by_id(incident_id)

    def list_incidents(self) -> list[Incident]:
        """Lista todos los incidentes registrados."""
        return self._repository.list_all()
