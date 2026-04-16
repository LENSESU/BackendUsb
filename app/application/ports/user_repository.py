"""Puerto (interfaz) para persistencia de Users. Lo implementa la infraestructura."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities import User


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
        """Obtiene un User por su email."""
        ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """Guarda o actualiza un User."""
        ...

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> UserBasicData | None:
        """Obtiene datos básicos de un usuario por su ID."""
        ...
