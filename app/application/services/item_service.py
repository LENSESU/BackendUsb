"""Caso de uso: operaciones sobre Items. Depende del puerto, no de implementaciones.

Modificación para #63 (Validar accesos cruzados):
  ``create_item()`` ahora acepta un parámetro opcional ``owner_id`` que se
  propaga a la entidad ``Item``.  La ruta POST de items inyecta el user_id
  del JWT como owner_id al llamar a este servicio.
"""

from uuid import UUID

from app.application.ports import ItemRepositoryPort
from app.domain.entities import Item


class ItemService:
    """Servicio de aplicación para Items. Orquesta dominio y puertos."""

    def __init__(self, repository: ItemRepositoryPort) -> None:
        self._repository = repository

    def get_item(self, item_id: UUID) -> Item | None:
        return self._repository.get_by_id(item_id)

    def list_items(self) -> list[Item]:
        return self._repository.list_all()

    def create_item(
        self,
        name: str,
        description: str | None = None,
        # [NUEVO – #63] owner_id se inyecta desde el JWT del usuario autenticado
        owner_id: UUID | None = None,
    ) -> Item:
        from uuid import uuid4

        item = Item(
            id=uuid4(), name=name.strip(), description=description, owner_id=owner_id
        )
        return self._repository.save(item)

    def delete_item(self, item_id: UUID) -> bool:
        return self._repository.delete(item_id)
