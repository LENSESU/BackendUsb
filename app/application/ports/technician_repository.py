"""Puerto (interfaz) para persistencia de técnicos."""

from abc import ABC, abstractmethod

from app.domain.entities.incident import Incident
from app.domain.entities.user import User


class TechnicianRepositoryPort(ABC):
    """Contrato de acceso a datos para usuarios con rol de técnico."""

    @abstractmethod
    def find_all(self) -> list[User]:
        """Retorna todos los técnicos (activos e inactivos)."""
        ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        """Retorna un técnico por ID, o None si no existe o no es técnico."""
        ...

    @abstractmethod
    def technician_available_list_all(self) -> list[User]:
        """Retorna técnicos activos sin carga activa (disponibles)."""
        ...

    @abstractmethod
    def assign_technician_to_incident(
        self,
        technician_id: str,
        incident_id: str,
        assigned_by_admin_id: str | None = None,
    ) -> User | None:
        """Asigna un técnico activo a un incidente; retorna el técnico o
        None si falla."""
        ...

    @abstractmethod
    def create_technician(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
    ) -> User:
        """
        Crea un usuario con rol Technician y lo persiste.

        Raises:
            ValueError: Si el email ya existe en el sistema.
        """
        ...

    @abstractmethod
    def update_technician(
        self,
        user_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> User | None:
        """
        Actualiza los campos provistos de un técnico.

        Retorna el técnico actualizado, o None si no existe.
        Raises:
            ValueError: Si el nuevo email ya pertenece a otro usuario.
        """
        ...

    @abstractmethod
    def set_active_status(self, user_id: str, is_active: bool) -> User | None:
        """
        Activa o desactiva un técnico.

        Retorna el técnico actualizado, o None si no existe.
        """
        ...

    @abstractmethod
    def find_incidents_by_technician(self, user_id: str) -> list[Incident]:
        """
        Retorna todos los incidentes asignados a un técnico, ordenados
        por fecha de creación descendente.
        """
        ...
