"""Puerto (interfaz) para persistencia de Users. Lo implementa la infraestructura."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import Role, User


@dataclass
class UserBasicData:
    """Datos básicos de un usuario."""

    id: UUID
    first_name: str
    last_name: str
    email: str


class UserRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Users."""

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Obtiene un User por su email (async — para servicios async)."""
        ...

    @abstractmethod
    def get_by_email_sync(self, email: str) -> User | None:
        """Obtiene un User por su email (síncrono — para auth)."""
        ...

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> UserBasicData | None:
        """Obtiene datos básicos de un usuario por su ID."""
        ...

    @abstractmethod
    def get_role_name_by_id(self, role_id: UUID) -> str | None:
        """Resuelve el nombre del rol dado su UUID. Retorna None si no existe."""
        ...

    @abstractmethod
    def get_role_by_name(self, name: str) -> Role | None:
        """Resuelve un Role completo por su nombre. Retorna None si no existe."""
        ...

    @abstractmethod
    def get_role_by_id(self, role_id: UUID) -> Role | None:
        """Resuelve un Role completo por su UUID. Retorna None si no existe."""
        ...

    @abstractmethod
    def delete_sync(self, user: User) -> None:
        """Elimina un User de la persistencia (síncrono)."""
        ...

    @abstractmethod
    def save_sync(self, user: User) -> User:
        """Guarda o actualiza un User (síncrono — para auth/register)."""
        ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """Guarda o actualiza un User (async)."""
        ...
