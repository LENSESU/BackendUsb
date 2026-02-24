"""Caso de uso: operaciones sobre Items. Depende del puerto, no de implementaciones."""

from uuid import UUID

from app.domain.entities import Item
from app.application.ports import ItemRepositoryPort


class ItemService:
    """Servicio de aplicación para Items. Orquesta dominio y puertos."""

    def __init__(self, repository: ItemRepositoryPort) -> None:
        self._repository = repository

    def get_item(self, item_id: UUID) -> Item | None:
        return self._repository.get_by_id(item_id)

    def list_items(self) -> list[Item]:
        return self._repository.list_all()

    def create_item(self, name: str, description: str | None = None) -> Item:
        from uuid import uuid4

        item = Item(id=uuid4(), name=name.strip(), description=description)
        return self._repository.save(item)

    def delete_item(self, item_id: UUID) -> bool:
        return self._repository.delete(item_id)
