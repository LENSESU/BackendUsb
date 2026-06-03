# app/api/routes/areas_inhabilitadas.py
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.area_inhabilitada import get_area_inhabilitada_service
from app.api.dependencies.auth import (
    get_current_role_name,
    get_current_user_id,
    require_role,
)
from app.api.dependencies.incident import get_incident_service
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

_ESTADOS_ACTIVOS = {"Nuevo", "En_proceso"}


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


def _validar_incidente_para_tecnico(
    incidente_id: UUID,
    current_user_id: UUID,
    incident_service,
) -> None:
    """Verifica que el incidente pertenece al técnico y no está Resuelto."""
    incidente = incident_service.get_incident(incidente_id)
    if incidente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado.",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )
    if incidente.technician_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Solo puedes operar sobre incidentes asignados a ti.",
                "error_code": "AREA_INCIDENT_NOT_ASSIGNED",
            },
        )
    if incidente.status not in _ESTADOS_ACTIVOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": (
                    "No se puede asociar un área a un incidente ya finalizado."
                ),
                "error_code": "AREA_INCIDENT_ALREADY_RESOLVED",
            },
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
    solo_activas: bool = Query(default=False),
    lugar_campus: str | None = Query(
        default=None,
        description="Filtrar por zona del campus (útil para sugerir al técnico)",
    ),
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> AreaInhabilitadaListResponse:
    if lugar_campus is not None:
        # Filtro específico: áreas activas para esa zona (sugerencia UX)
        items = [_to_response(a) for a in service.listar_por_lugar(lugar_campus)]
    else:
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
    dependencies=[Depends(require_role("Administrator", "Technician"))],
    summary="Registrar área inhabilitada",
)
def registrar_area(
    payload: AreaInhabilitadaCreate,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
    incidente_area_service: IncidenteAreaService = Depends(get_incidente_area_service),
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> AreaInhabilitadaResponse:
    incident_service = get_incident_service()

    # Técnico: debe proveer incidente_id y el incidente debe ser suyo y activo
    if current_role == "Technician":
        if payload.incidente_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": (
                        "Un técnico debe indicar el incidente asociado al registrar "
                        "un área inhabilitada."
                    ),
                    "error_code": "AREA_INCIDENT_REQUIRED",
                },
            )
        _validar_incidente_para_tecnico(
            payload.incidente_id, current_user_id, incident_service
        )

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
            registrada_por_id=current_user_id,  # ← siempre se guarda el autor
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "error_code": "AREA_INHABILITADA_INVALID"},
        ) from e

    # Asociar el incidente automáticamente si se proporcionó
    if payload.incidente_id is not None:
        try:
            incidente_area_service.asociar(
                incidente_id=payload.incidente_id,
                area_id=area.id,
            )
        except ValueError:
            pass  # Ya estaba asociado — no es error en este flujo

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
            detail={
                "message": f"Área inhabilitada con id {area_id} no encontrada.",
                "error_code": "AREA_INHABILITADA_NOT_FOUND",
            },
        )
    return _to_response(area)


@router.patch(
    "/{area_id}",
    response_model=AreaInhabilitadaResponse,
    dependencies=[Depends(require_role("Administrator", "Technician"))],
    summary="Actualizar área inhabilitada",
)
def actualizar_area(
    area_id: UUID,
    payload: AreaInhabilitadaUpdate,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> AreaInhabilitadaResponse:
    try:
        area = service.actualizar(
            area_id=str(area_id),
            solicitante_id=current_user_id,
            es_admin=(current_role == "Administrator"),
            **payload.model_dump(exclude_unset=True),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(e), "error_code": "AREA_EDIT_FORBIDDEN"},
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": str(e), "error_code": "AREA_INHABILITADA_INVALID"},
        ) from e
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"Área inhabilitada con id {area_id} no encontrada.",
                "error_code": "AREA_INHABILITADA_NOT_FOUND",
            },
        )
    return _to_response(area)


@router.delete(
    "/{area_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator"))],  # ← solo admin elimina
    summary="Eliminar área inhabilitada",
)
def eliminar_area(
    area_id: UUID,
    service: AreaInhabilitadaService = Depends(get_area_inhabilitada_service),
) -> None:
    if not service.eliminar(str(area_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": f"Área inhabilitada con id {area_id} no encontrada.",
                "error_code": "AREA_INHABILITADA_NOT_FOUND",
            },
        )


# ---------------------------------------------------------------------------
# Asociación área ↔ incidente
# ---------------------------------------------------------------------------


@router.post(
    "/{area_id}/incidentes",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator", "Technician"))],
    summary="Asociar un incidente a un área inhabilitada",
)
def asociar_incidente(
    area_id: UUID,
    payload: AsociarIncidenteRequest,
    service: IncidenteAreaService = Depends(get_incidente_area_service),
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> dict:
    # Técnico: valida que el incidente sea suyo y esté activo
    if current_role == "Technician":
        incident_service = get_incident_service()
        _validar_incidente_para_tecnico(
            payload.incidente_id, current_user_id, incident_service
        )
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
            status.HTTP_409_CONFLICT
            if "ya está asociado" in msg
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(
            status_code=http_status, detail={"message": msg, "error_code": code}
        ) from e
    return {"message": "Incidente asociado al área inhabilitada correctamente."}


@router.delete(
    "/{area_id}/incidentes/{incidente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator"))],  # ← solo admin desasocia
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
            detail={
                "message": "Asociación no encontrada.",
                "error_code": "ASOCIACION_NOT_FOUND",
            },
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
