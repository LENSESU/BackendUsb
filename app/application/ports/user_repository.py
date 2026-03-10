"""Puerto (interfaz) para persistencia de Users. Lo implementa la infraestructura."""

from abc import ABC, abstractmethod

from app.domain.entities import User


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
