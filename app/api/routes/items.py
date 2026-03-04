"""Rutas HTTP para Items. Traduce request/response y delega en el caso de uso."""

from uuid import UUID

from fastapi import APIRouter

from app.api.schemas import ItemCreate, ItemResponse
from app.core.exceptions import NotFoundError
from app.application.ports import ItemRepositoryPort
from app.application.services import ItemService

router = APIRouter()


_repository: ItemRepositoryPort | None = None


def get_item_service() -> ItemService:
    """Obtiene el servicio de Items (en producción vendría de un contenedor de DI)."""
    global _repository
    from app.infrastructure.adapters import InMemoryItemRepository

    if _repository is None:
        _repository = InMemoryItemRepository()
    return ItemService(repository=_repository)


@router.get("/", response_model=list[ItemResponse])
def list_items() -> list[ItemResponse]:
    service = get_item_service()
    items = service.list_items()
    return [ItemResponse.model_validate(i) for i in items]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: UUID) -> ItemResponse:
    service = get_item_service()
    item = service.get_item(item_id)
    if item is None:
        raise NotFoundError("Item no encontrado")
    return ItemResponse.model_validate(item)


@router.post("/", response_model=ItemResponse, status_code=201)
def create_item(payload: ItemCreate) -> ItemResponse:
    service = get_item_service()
    item = service.create_item(name=payload.name, description=payload.description)
    return ItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: UUID) -> None:
    service = get_item_service()
    if not service.delete_item(item_id):
        raise NotFoundError("Item no encontrado")
