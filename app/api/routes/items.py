"""Rutas HTTP para Items. Traduce request/response y delega en el caso de uso.

Modificaciones para #61 y #63:

- **#61 – Proteger endpoints del backend:**
  Los 4 endpoints (GET list, GET by id, POST create, DELETE) ahora
  requieren un JWT válido con un rol autorizado.  Se aplica mediante
  ``dependencies=[Depends(require_role("Administrator", "Student", "Technician"))]``
  en cada ruta.  Sin token → 403; token inválido/expirado → 401.

- **#63 – Validar accesos cruzados (ownership):**
  * ``POST /``:  el ``owner_id`` del item se asigna automáticamente con el
    ``user_id`` extraído del JWT (``Depends(get_current_user_id)``).
  * ``DELETE /{item_id}``:  se compara ``item.owner_id`` contra el usuario
    autenticado.  Si no coinciden y el rol NO es "Administrator", se
    devuelve **403 CROSS_ACCESS_DENIED**.  Un Administrator puede eliminar
    cualquier item (bypass de ownership).

Archivos relacionados que también fueron modificados:
  - ``app/domain/entities/item.py``       → +campo ``owner_id``
  - ``app/api/schemas/item.py``           → +campo ``owner_id`` en respuesta
  - ``app/application/services/item_service.py`` → ``create_item`` acepta ``owner_id``
  - ``app/api/dependencies/auth.py``      → +``get_current_role_name``,
                                              +``require_role``
  - ``app/api/routes/auth.py``            → login/refresh incluyen ``role_name`` en JWT
  - ``tests/api/test_items_protected.py`` → 18 tests para #61 y #63
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import (
    get_current_role_name,
    get_current_user_id,
    require_role,
)
from app.api.schemas import ItemCreate, ItemResponse
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


# ---------------------------------------------------------------------------
# [#61] Todos los endpoints llevan dependencies=[Depends(require_role(...))]
# para exigir JWT válido + rol autorizado.  Sin token → 403, token malo → 401.
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[ItemResponse],
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_items() -> list[ItemResponse]:
    """Lista todos los items.  [#61] Requiere autenticación con cualquier rol."""
    service = get_item_service()
    items = service.list_items()
    return [ItemResponse.model_validate(i) for i in items]


@router.get(
    "/{item_id}",
    response_model=ItemResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_item(item_id: UUID) -> ItemResponse:
    """Obtiene un item por ID.  [#61] Requiere autenticación con cualquier rol."""
    service = get_item_service()
    item = service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return ItemResponse.model_validate(item)


@router.post(
    "/",
    response_model=ItemResponse,
    status_code=201,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def create_item(
    payload: ItemCreate,
    # [#63] Se inyecta el user_id del token para asignarlo como owner_id
    current_user_id: UUID = Depends(get_current_user_id),
) -> ItemResponse:
    """Crea un nuevo item.  [#61] Requiere auth.  [#63] Asigna owner_id del JWT."""
    service = get_item_service()
    item = service.create_item(
        name=payload.name,
        description=payload.description,
        owner_id=current_user_id,
    )
    return ItemResponse.model_validate(item)


@router.delete(
    "/{item_id}",
    status_code=204,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def delete_item(
    item_id: UUID,
    # [#63] Se inyectan user_id y role_name para validación de ownership
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> None:
    """
    Elimina un item.  [#61] Requiere autenticación.

    [#63] Validación de acceso cruzado (ownership):
    - Si el item tiene ``owner_id`` y NO coincide con el usuario actual:
      - Si el rol es "Administrator" → se permite (bypass).
      - Si el rol es cualquier otro  → **403 CROSS_ACCESS_DENIED**.
    - Si el item no tiene ``owner_id`` (legacy) → se permite a cualquiera.
    - Si el usuario ES el dueño → se permite.
    """
    service = get_item_service()
    item = service.get_item(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    # [#63] Validación de acceso cruzado (ownership):
    # Si el item tiene dueño y el solicitante no es el dueño,
    # solo un Administrator puede hacer bypass.
    if item.owner_id is not None and item.owner_id != current_user_id:
        if current_role != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "No puede eliminar un item que no le pertenece",
                    "error_code": "CROSS_ACCESS_DENIED",
                },
            )

    if not service.delete_item(item_id):
        raise HTTPException(status_code=404, detail="Item no encontrado")
