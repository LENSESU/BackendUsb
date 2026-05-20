"""Rutas HTTP para incidentes."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies.auth import (
    get_current_role_name,
    get_current_user_id,
    require_role,
)
from app.api.dependencies.incident import get_incident_service
from app.api.dependencies.incident_category import get_incident_category_service
from app.api.dependencies.storage import (
    get_file_repository,
    get_incident_evidence_service,
)
from app.api.dependencies.technician import get_technician_service
from app.api.schemas import (
    AdminIncidentSummary,
    AssignTechnicianRequest,
    CriticalZoneResponse,
    IncidentCreate,
    IncidentDetailResponse,
    IncidentEvidenceUploadResponse,
    IncidentGeoMarker,
    IncidentResponse,
    IncidentStatusUpdate,
    IncidentUpdate,
    PaginatedAdminIncidentsResponse,
    PaginatedIncidentsGeoResponse,
    PaginatedIncidentsResponse,
)
from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.application.services.technician_service import TechnicianService
from app.domain.entities.incident import (
    PRIORITY_SORT_WEIGHT,
    EvidencePhotoType,
    Incident,
)

router = APIRouter()

_DEFAULT_PRIORITY_WEIGHT = max(PRIORITY_SORT_WEIGHT.values()) + 1


def _reraise_service_unprocessable(exc: HTTPException) -> None:
    """Re-lanza errores 422 del servicio conservando ``detail`` con ``error_code``."""
    if exc.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY:
        raise exc
    if isinstance(exc.detail, dict):
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    raise HTTPException(
        status_code=exc.status_code,
        detail={
            "message": str(exc.detail),
            "error_code": "INCIDENT_CATEGORY_INVALID",
        },
    ) from exc


def _incident_to_response(incident: Incident) -> IncidentResponse:
    location = incident.location
    file_repo = get_file_repository()

    before_photo_url = None
    if incident.before_photo_id:
        before_photo_url = file_repo.get_by_id(incident.before_photo_id)

    after_photo_url = None
    if incident.after_photo_id:
        after_photo_url = file_repo.get_by_id(incident.after_photo_id)

    return IncidentResponse(
        id=incident.id,
        student_id=incident.student_id,
        technician_id=incident.technician_id,
        category_id=incident.category_id,
        description=incident.description,
        campus_place=location.campus_place if location else None,
        latitude=location.latitude if location else None,
        longitude=location.longitude if location else None,
        status=incident.status,
        priority=incident.priority,
        before_photo_id=incident.before_photo_id,
        after_photo_id=incident.after_photo_id,
        before_photo_url=before_photo_url,
        after_photo_url=after_photo_url,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


def _incident_patch_kwargs(payload: IncidentUpdate) -> dict:
    raw = payload.model_dump(exclude_unset=True)
    key_map = {
        "tecnico_id": "technician_id",
        "categoria_id": "category_id",
        "descripcion": "description",
        "lugar_campus": "campus_place",
        "latitud": "latitude",
        "longitud": "longitude",
        "prioridad": "priority",
        "foto_antes_id": "before_photo_id",
        "foto_despues_id": "after_photo_id",
    }
    return {key_map[k]: v for k, v in raw.items() if k in key_map}


def _incident_to_admin_summary(incident: Incident) -> AdminIncidentSummary:
    loc = incident.location
    return AdminIncidentSummary(
        id=incident.id,
        category_id=incident.category_id,
        technician_id=incident.technician_id,
        status=incident.status,
        priority=incident.priority,
        created_at=incident.created_at,
        location=loc.campus_place if loc else None,
        reported_by=incident.student_id,
        reporter_email=incident.reporter_email,
    )


def _incident_to_geo_marker(
    incident: Incident, category_name: str | None = None
) -> IncidentGeoMarker | None:
    """Convierte un incidente a un marcador geográfico.

    Retorna None si el incidente no tiene coordenadas válidas.
    """
    location = incident.location
    if location is None or location.latitude is None or location.longitude is None:
        return None

    return IncidentGeoMarker(
        id=incident.id,
        category_name=category_name or "Sin categoría",
        status=incident.status,
        priority=incident.priority,
        latitude=location.latitude,
        longitude=location.longitude,
        campus_place=location.campus_place,
        created_at=incident.created_at,
    )


@router.get(
    "/admin-inbox",
    response_model=PaginatedAdminIncidentsResponse,
    dependencies=[Depends(require_role("Administrator"))],
)
def list_incidents_admin_inbox(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    order_by: str | None = Query(default=None, pattern="^(status|priority)$"),
) -> PaginatedAdminIncidentsResponse:
    """Bandeja del administrador: lista paginada de todos los incidentes,
    ordenados del más reciente al más antiguo (ordenamiento en base de datos)."""
    service = get_incident_service()
    incidents = service.list_incidents()
    if order_by == "status":
        incidents = sorted(incidents, key=lambda i: i.status)
    elif order_by == "priority":
        incidents = sorted(
            incidents,
            key=lambda i: PRIORITY_SORT_WEIGHT.get(
                i.priority, _DEFAULT_PRIORITY_WEIGHT
            ),
        )
    total = len(incidents)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    return PaginatedAdminIncidentsResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=[_incident_to_admin_summary(i) for i in incidents[start:end]],
    )


@router.get(
    "/critical-zones",
    response_model=list[CriticalZoneResponse],
    dependencies=[Depends(require_role("Administrator"))],
)
def get_critical_zones() -> list[CriticalZoneResponse]:
    """Retorna zonas del campus agrupadas por concentración de incidentes,
    ponderadas por prioridad y ordenadas de más a menos crítica."""
    service = get_incident_service()
    zones = service.get_critical_zones()
    return [CriticalZoneResponse(**z) for z in zones]


@router.get(
    "/",
    response_model=PaginatedIncidentsResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_incidents(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    estado: str | None = Query(
        default=None,
        description="Filtrar por estado: Nuevo, En_proceso, Resuelto",
    ),
    categoria_id: UUID | None = Query(
        default=None, description="Filtrar por ID de categoría"
    ),
    prioridad: str | None = Query(
        default=None, description="Filtrar por prioridad"
    ),
    fecha_inicio: datetime | None = Query(
        default=None, description="Filtrar desde esta fecha (ISO 8601)"
    ),
    fecha_fin: datetime | None = Query(
        default=None, description="Filtrar hasta esta fecha (ISO 8601)"
    ),
    order_by: str | None = Query(default=None, pattern="^(status|priority)$"),
) -> PaginatedIncidentsResponse:
    service = get_incident_service()
    incidents = service.list_incidents(
        status=estado,
        category_id=categoria_id,
        priority=prioridad,
        date_from=fecha_inicio,
        date_to=fecha_fin,
    )
    if order_by == "status":
        incidents = sorted(incidents, key=lambda i: i.status)
    elif order_by == "priority":
        incidents = sorted(
            incidents,
            key=lambda i: PRIORITY_SORT_WEIGHT.get(
                i.priority, _DEFAULT_PRIORITY_WEIGHT
            ),
        )
    total = len(incidents)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    return PaginatedIncidentsResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=[_incident_to_response(i) for i in incidents[start:end]],
    )


@router.get(
    "/geo",
    response_model=PaginatedIncidentsGeoResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_incidents_geo(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
) -> PaginatedIncidentsGeoResponse:
    """Consulta geográfica de incidentes para visualización en mapas.

    Retorna solo los incidentes que poseen coordenadas geográficas válidas.
    Cada marcador incluye información optimizada para carga eficiente:
    - Identificador del incidente
    - Nombre de categoría
    - Estado y prioridad
    - Coordenadas (latitud, longitud)
    - Ubicación en campus
    - Fecha de creación
    """
    service = get_incident_service()
    category_service = get_incident_category_service()

    # Obtener todos los incidentes
    all_incidents = service.list_incidents()

    # Filtrar solo incidentes con coordenadas válidas y convertir a marcadores
    geo_markers = []
    for incident in all_incidents:
        marker = _incident_to_geo_marker(incident)
        if marker is not None:
            # Enriquecer con nombre de la categoría
            category = category_service.get_by_id(str(incident.category_id))
            if category:
                marker.category_name = category.name
            geo_markers.append(marker)

    # Aplicar paginación
    total = len(geo_markers)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit

    return PaginatedIncidentsGeoResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=geo_markers[start:end],
    )


@router.get(
    "/{incident_id}/geo",
    response_model=IncidentGeoMarker,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_incident_geo(incident_id: UUID) -> IncidentGeoMarker:
    """Consulta geográfica de un incidente específico.

    Retorna los datos geográficos de un incidente para su visualización
    en mapas. Solo disponible si el incidente posee coordenadas válidas.

    Campos incluidos:
    - ID del incidente
    - Nombre de categoría
    - Estado y prioridad
    - Coordenadas (latitud, longitud)
    - Ubicación en campus
    - Fecha de creación
    """
    service = get_incident_service()
    incident = service.get_incident(incident_id)

    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )

    # Convertir a marcador geográfico
    marker = _incident_to_geo_marker(incident)
    if marker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": ("El incidente no posee coordenadas geográficas válidas"),
                "error_code": "INCIDENT_NO_GEO_DATA",
            },
        )

    # Enriquecer con nombre de la categoría
    category_service = get_incident_category_service()
    category = category_service.get_by_id(str(incident.category_id))
    if category:
        marker.category_name = category.name

    return marker


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_incident(incident_id: UUID) -> IncidentDetailResponse:
    service = get_incident_service()
    incident_with_details = service.get_incident_with_details(incident_id)
    if incident_with_details is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )

    incident = incident_with_details.incident
    location = incident.location
    file_repo = get_file_repository()

    before_photo_url = None
    if incident.before_photo_id:
        before_photo_url = file_repo.get_by_id(incident.before_photo_id)

    after_photo_url = None
    if incident.after_photo_id:
        after_photo_url = file_repo.get_by_id(incident.after_photo_id)

    return IncidentDetailResponse(
        id=incident.id,
        student_id=incident.student_id,
        technician_id=incident.technician_id,
        category_id=incident.category_id,
        description=incident.description,
        campus_place=location.campus_place if location else None,
        latitude=location.latitude if location else None,
        longitude=location.longitude if location else None,
        status=incident.status,
        priority=incident.priority,
        before_photo_id=incident.before_photo_id,
        after_photo_id=incident.after_photo_id,
        before_photo_url=before_photo_url,
        after_photo_url=after_photo_url,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        student_first_name=incident_with_details.student_first_name,
        student_last_name=incident_with_details.student_last_name,
        student_email=incident_with_details.student_email,
        technician_first_name=incident_with_details.technician_first_name,
        technician_last_name=incident_with_details.technician_last_name,
        technician_email=incident_with_details.technician_email,
    )


@router.post(
    "/",
    response_model=IncidentResponse,
    status_code=201,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def create_incident(
    payload: IncidentCreate,
    current_user_id: UUID = Depends(get_current_user_id),
) -> IncidentResponse:
    """Crea un incidente usando el usuario autenticado como student_id."""
    service = get_incident_service()

    try:
        incident = service.create_incident(
            student_id=current_user_id,
            category_id=payload.categoria_id,
            description=payload.descripcion,
            before_photo_id=payload.foto_antes_id,
            campus_place=payload.lugar_campus,
            latitude=payload.latitud,
            longitude=payload.longitud,
            priority=payload.prioridad,
            status=payload.estado,
        )
    except HTTPException as e:
        _reraise_service_unprocessable(e)

    return _incident_to_response(incident)


@router.post(
    "/{incident_id}/technician",
    response_model=IncidentResponse,
    dependencies=[Depends(require_role("Administrator", "Technician"))],
)
def assign_technician_to_incident(
    incident_id: UUID,
    payload: AssignTechnicianRequest,
    technician_service: TechnicianService = Depends(get_technician_service),
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> IncidentResponse:
    """Asocia un técnico activo con rol adecuado a un incidente existente."""
    incident = technician_service.assign_technician_to_incident(
        incident_id=incident_id,
        technician_id=payload.tecnico_id,
        assigned_by_admin_id=(
            current_user_id if current_role == "Administrator" else None
        ),
    )
    return _incident_to_response(incident)


@router.patch(
    "/{incident_id}/status",
    response_model=IncidentResponse,
    dependencies=[Depends(require_role("Administrator", "Technician"))],
)
def update_incident_status(
    incident_id: UUID,
    payload: IncidentStatusUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> IncidentResponse:
    """Transiciona el estado de un incidente (Nuevo → En_proceso → Resuelto).

    Solo Technician (asignado) y Administrator pueden cambiar el estado.
    """
    service = get_incident_service()
    existing = service.get_incident(incident_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )
    if current_role == "Technician" and existing.technician_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": (
                    "Solo el técnico asignado puede cambiar el estado del incidente"
                ),
                "error_code": "INCIDENT_STATUS_NOT_ASSIGNED",
            },
        )
    try:
        updated = service.update_incident(incident_id, status=payload.estado.value)
    except HTTPException as e:
        _reraise_service_unprocessable(e)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )
    return _incident_to_response(updated)


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def patch_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> IncidentResponse:
    service = get_incident_service()
    existing = service.get_incident(incident_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )
    raw = payload.model_dump(exclude_unset=True)
    if current_role == "Student":
        if existing.student_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "No puede modificar un incidente que no le pertenece",
                    "error_code": "INCIDENT_CROSS_ACCESS_DENIED",
                },
            )
        if "tecnico_id" in raw:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": (
                        "Solo personal autorizado puede asignar o cambiar el técnico"
                    ),
                    "error_code": "INCIDENT_TECHNICIAN_UPDATE_FORBIDDEN",
                },
            )
    kwargs = _incident_patch_kwargs(payload)
    try:
        updated = service.update_incident(incident_id, **kwargs)
    except HTTPException as e:
        _reraise_service_unprocessable(e)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )
    return _incident_to_response(updated)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def delete_incident(
    incident_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> None:
    service = get_incident_service()
    existing = service.get_incident(incident_id)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )
    if current_role not in ("Administrator", "Technician"):
        if existing.student_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "No puede eliminar un incidente que no le pertenece",
                    "error_code": "INCIDENT_CROSS_ACCESS_DENIED",
                },
            )
    if not service.delete_incident(incident_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Incidente no encontrado",
                "error_code": "INCIDENT_NOT_FOUND",
            },
        )


@router.post(
    "/{incident_id}/evidence",
    response_model=IncidentEvidenceUploadResponse,
    status_code=201,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
async def upload_incident_evidence(
    incident_id: UUID,
    photo: UploadFile = File(...),
    photo_type: EvidencePhotoType = Query(
        default=EvidencePhotoType.BEFORE,
        description=(
            "Tipo de evidencia: 'before' para la foto inicial (reporte), "
            "'after' para la foto final (cierre del incidente)."
        ),
    ),
    evidence_service: IncidentEvidenceService = Depends(get_incident_evidence_service),
    current_user_id: UUID = Depends(get_current_user_id),
    current_role: str = Depends(get_current_role_name),
) -> IncidentEvidenceUploadResponse:
    """Valida y carga una evidencia fotográfica para un incidente.

    - ``photo_type=before``: foto inicial cargada por el estudiante al reportar.
    - ``photo_type=after``: foto final de cierre (HU-E5-028). Solo puede subirla
      el técnico asignado al incidente o un Administrator, y solo cuando el
      incidente está en estado ``En_proceso`` o ``Resuelto``.
    """
    if photo_type == EvidencePhotoType.AFTER:
        if current_role == "Student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": (
                        "Solo el técnico asignado o un administrador puede subir "
                        "la foto de evidencia final."
                    ),
                    "error_code": "INCIDENT_AFTER_PHOTO_FORBIDDEN",
                },
            )
        if current_role == "Technician":
            service = get_incident_service()
            existing = service.get_incident(incident_id)
            if existing is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "Incidente no encontrado",
                        "error_code": "INCIDENT_NOT_FOUND",
                    },
                )
            if existing.technician_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "message": (
                            "Solo el técnico asignado puede subir la foto final "
                            "del incidente."
                        ),
                        "error_code": "INCIDENT_AFTER_PHOTO_NOT_ASSIGNED",
                    },
                )

    stored_file = await evidence_service.upload_evidence(
        incident_id=incident_id,
        file=photo,
        photo_type=photo_type,
    )

    message = (
        "Foto de evidencia final cargada correctamente"
        if photo_type == EvidencePhotoType.AFTER
        else "Evidencia fotográfica cargada correctamente"
    )
    return IncidentEvidenceUploadResponse(
        incident_id=incident_id,
        filename=photo.filename or "",
        content_type=(photo.content_type or "").lower(),
        storage_object_name=stored_file.object_name,
        file_url=stored_file.file_url,
        message=message,
    )
