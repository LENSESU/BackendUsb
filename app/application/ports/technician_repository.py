"""Puerto (interfaz) para persistencia de técnicos.

PSDT: Falta método de retiro de asignación de técnico a incidente.
"""

from abc import ABC, abstractmethod

from app.domain.entities.user import User


class TechnicianRepositoryPort(ABC):
    """Contrato de acceso a datos para usuarios con rol de técnico."""

    @abstractmethod
    def find_all(self) -> list[User]:
        """Retorna todos los técnicos registrados (por rol, sin filtrar
        disponibilidad)."""
        ...

    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        """Retorna un técnico por ID de usuario, o None si no existe o no es técnico."""
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
    def technician_available_list_all(self) -> list[User]:
        """Retorna técnicos activos considerados disponibles (sin carga activa)."""
        ...
