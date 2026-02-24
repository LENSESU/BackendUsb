"""Puerto (interfaz) para persistencia de Items. Lo implementa la infraestructura."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities import Item


class ItemRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de Items."""

    @abstractmethod
    def get_by_id(self, item_id: UUID) -> Item | None:
        """Obtiene un Item por su ID."""
        ...

    @abstractmethod
    def list_all(self) -> list[Item]:
        """Lista todos los Items."""
        ...

    @abstractmethod
    def save(self, item: Item) -> Item:
        """Guarda o actualiza un Item."""
        ...

    @abstractmethod
    def delete(self, item_id: UUID) -> bool:
        """Elimina un Item por ID. Retorna True si existía."""
        ...
