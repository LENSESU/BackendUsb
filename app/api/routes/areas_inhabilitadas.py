from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.area_inhabilitada import get_area_inhabilitada_service
from app.api.dependencies.auth import require_role
from app.api.dependencies.incidente_area import get_incidente_area_service
from app.api.schemas.area_inhabilitada import (
    AreaAsociadaResponse,
    AreaInhabilitadaCreate,
    AreaInhabilitadaListResponse,
    AreaInhabilitadaResponse,
    AreaInhabilitadaUpdate,
    AsociarIncidenteRequest,
    IncidenteAsociadoResponse,
)
from app.application.services.area_inhabilitada_service import AreaInhabilitadaService
from app.application.services.incidente_area_service import IncidenteAreaService

router = APIRouter()


def _to_response(area) -> AreaInhabilitadaResponse:
    return AreaInhabilitadaResponse(
        id=area.id,
        nombre=area.nombre,
        motivo=area.motivo,
        descripcion=area.descripcion,
        fecha_inicio=area.fecha_inicio,
        fecha_fin=area.fecha_fin,
        activa=area.activa,
        lugar_campus=area.lugar_campus,
        latitud=area.latitud,
        longitud=area.longitud,
        registrada_por_id=area.registrada_por_id,
        created_at=area.created_at,
        updated_at=area.updated_at,
    )


@router.get(
    "/",
    response_model=AreaInhabilitadaListResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
    summary="Listar áreas inhabilitadas",
)
def listar_areas(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    solo_activas: bool = Query(default=False, description="Filtrar solo áreas actualmente inhabilitadas"),
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> AreaInhabilitadaListResponse:
    items = [_to_response(a) for a in service.listar(solo_activas=solo_activas)]
    total = len(items)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    return AreaInhabilitadaListResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=items[start : start + limit],
    )


@router.post(
    "/",
    response_model=AreaInhabilitadaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator"))],
    summary="Registrar área inhabilitada",
)
def registrar_area(
    payload: AreaInhabilitadaCreate,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> AreaInhabilitadaResponse:
    try:
        area = service.registrar(
            nombre=payload.nombre,
            motivo=payload.motivo,
            fecha_inicio=payload.fecha_inicio,
            descripcion=payload.descripcion,
            fecha_fin=payload.fecha_fin,
            lugar_campus=payload.lugar_campus,
            latitud=payload.latitud,
            longitud=payload.longitud,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "error_code": "AREA_INHABILITADA_INVALID"},
        ) from e
    return _to_response(area)


@router.get(
    "/{area_id}",
    response_model=AreaInhabilitadaResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
    summary="Consultar área inhabilitada por ID",
)
def obtener_area(
    area_id: UUID,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> AreaInhabilitadaResponse:
    area = service.obtener_por_id(str(area_id))
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Área inhabilitada con id {area_id} no encontrada.", "error_code": "AREA_INHABILITADA_NOT_FOUND"},
        )
    return _to_response(area)


@router.patch(
    "/{area_id}",
    response_model=AreaInhabilitadaResponse,
    dependencies=[Depends(require_role("Administrator"))],
    summary="Actualizar área inhabilitada",
)
def actualizar_area(
    area_id: UUID,
    payload: AreaInhabilitadaUpdate,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> AreaInhabilitadaResponse:
    try:
        area = service.actualizar(
            area_id=str(area_id),
            nombre=payload.nombre,
            motivo=payload.motivo,
            descripcion=payload.descripcion,
            fecha_inicio=payload.fecha_inicio,
            fecha_fin=payload.fecha_fin,
            activa=payload.activa,
            lugar_campus=payload.lugar_campus,
            latitud=payload.latitud,
            longitud=payload.longitud,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "error_code": "AREA_INHABILITADA_INVALID"},
        ) from e
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Área inhabilitada con id {area_id} no encontrada.", "error_code": "AREA_INHABILITADA_NOT_FOUND"},
        )
    return _to_response(area)


@router.delete(
    "/{area_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator"))],
    summary="Eliminar área inhabilitada",
)
def eliminar_area(
    area_id: UUID,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> None:
    if not service.eliminar(str(area_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": f"Área inhabilitada con id {area_id} no encontrada.", "error_code": "AREA_INHABILITADA_NOT_FOUND"},
        )


# ---------------------------------------------------------------------------
# Endpoints de asociación: área ↔ incidente
# ---------------------------------------------------------------------------


@router.post(
    "/{area_id}/incidentes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator"))],
    summary="Asociar un incidente a un área inhabilitada",
)
def asociar_incidente(
    area_id: UUID,
    payload: AsociarIncidenteRequest,
    service: IncidenteAreaService = Depends(get_incidente_area_service),
) -> dict:
    try:
        service.asociar(incidente_id=payload.incidente_id, area_id=area_id)
    except ValueError as e:
        msg = str(e)
        code = (
            "ASOCIACION_YA_EXISTE"
            if "ya está asociado" in msg
            else "AREA_O_INCIDENTE_NOT_FOUND"
        )
        http_status = (
            status.HTTP_409_CONFLICT if "ya está asociado" in msg else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=http_status, detail={"message": msg, "error_code": code}) from e
    return {"message": "Incidente asociado al área inhabilitada correctamente."}


@router.delete(
    "/{area_id}/incidentes/{incidente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator"))],
    summary="Desasociar un incidente de un área inhabilitada",
)
def desasociar_incidente(
    area_id: UUID,
    incidente_id: UUID,
    service: IncidenteAreaService = Depends(get_incidente_area_service),
) -> None:
    if not service.desasociar(incidente_id=incidente_id, area_id=area_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Asociación no encontrada.", "error_code": "ASOCIACION_NOT_FOUND"},
        )


@router.get(
    "/{area_id}/incidentes",
    response_model=list[IncidenteAsociadoResponse],
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
    summary="Listar incidentes asociados a un área inhabilitada",
)
def listar_incidentes_por_area(
    area_id: UUID,
    service: IncidenteAreaService = Depends(get_incidente_area_service),
) -> list[IncidenteAsociadoResponse]:
    incidents = service.obtener_incidentes_por_area(area_id=area_id)
    return [
        IncidenteAsociadoResponse(
            id=i.id,
            descripcion=i.description,
            status=i.status,
            priority=i.priority,
            campus_place=i.location.campus_place if i.location else None,
            created_at=i.created_at,
        )
        for i in incidents
    ]


@router.get(
    "/incidente/{incidente_id}/areas",
    response_model=list[AreaAsociadaResponse],
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
    summary="Listar áreas inhabilitadas asociadas a un incidente",
)
def listar_areas_por_incidente(
    incidente_id: UUID,
    service: IncidenteAreaService = Depends(get_incidente_area_service),
) -> list[AreaAsociadaResponse]:
    areas = service.obtener_areas_por_incidente(incidente_id=incidente_id)
    return [
        AreaAsociadaResponse(
            id=a.id,
            nombre=a.nombre,
            motivo=a.motivo,
            activa=a.activa,
            lugar_campus=a.lugar_campus,
            fecha_inicio=a.fecha_inicio,
            fecha_fin=a.fecha_fin,
        )
        for a in areas
    ]
