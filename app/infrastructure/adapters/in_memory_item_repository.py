"""Adaptador en memoria que implementa ItemRepositoryPort.
Se puede sustituir por SQL, NoSQL, etc."""

from uuid import UUID

from app.application.ports import ItemRepositoryPort
from app.domain.entities import Item


class InMemoryItemRepository(ItemRepositoryPort):
    """Implementación del puerto de Items usando un diccionario en memoria."""

    def __init__(self) -> None:
        self._storage: dict[UUID, Item] = {}

    def get_by_id(self, item_id: UUID) -> Item | None:
        return self._storage.get(item_id)

    def list_all(self) -> list[Item]:
        return list(self._storage.values())

    def save(self, item: Item) -> Item:
        self._storage[item.id] = item
        return item

    def delete(self, item_id: UUID) -> bool:
        if item_id in self._storage:
            del self._storage[item_id]
            return True
        return False
