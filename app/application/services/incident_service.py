"""Caso de uso: listado de incidentes para la bandeja del administrador."""

from app.application.ports import IncidentRepositoryPort
from app.domain.entities import Incident


class IncidentService:
    """Servicio de aplicación para Incidents. Orquesta dominio y puertos."""

    def __init__(self, repository: IncidentRepositoryPort) -> None:
        self._repository = repository

    def list_incidents(self) -> list[Incident]:
        """Retorna todos los incidentes ordenados del más reciente al más antiguo."""
        incidents = self._repository.list_all()
        return sorted(incidents, key=lambda i: i.created_at, reverse=True)
