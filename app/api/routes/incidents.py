"""Rutas HTTP para incidentes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies.auth import (
    get_current_role_name,
    get_current_user_id,
    require_role,
)
from app.api.dependencies.incident import get_incident_service
from app.api.dependencies.storage import get_incident_evidence_service
from app.api.dependencies.technician import get_technician_service
from app.api.schemas import (
    AdminIncidentSummary,
    AssignTechnicianRequest,
    IncidentCreate,
    IncidentDetailResponse,
    IncidentEvidenceUploadResponse,
    IncidentResponse,
    IncidentStatusUpdate,
    IncidentUpdate,
    PaginatedAdminIncidentsResponse,
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
    "/",
    response_model=PaginatedIncidentsResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_incidents(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    order_by: str | None = Query(default=None, pattern="^(status|priority)$"),
) -> PaginatedIncidentsResponse:
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
    return PaginatedIncidentsResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=[_incident_to_response(i) for i in incidents[start:end]],
    )


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
