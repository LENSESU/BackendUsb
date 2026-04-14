"""Rutas HTTP para incidentes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies.auth import (
    get_current_role_name,
    get_current_user_id,
    require_role,
)
from app.api.dependencies.storage import get_incident_evidence_service
from app.api.dependencies.technician import get_technician_service
from app.api.schemas import (
    AdminIncidentSummary,
    AssignTechnicianRequest,
    IncidentCreate,
    IncidentEvidenceUploadResponse,
    IncidentResponse,
    IncidentUpdate,
    PaginatedAdminIncidentsResponse,
    PaginatedIncidentsResponse,
)
from app.application.ports.incident_repository import IncidentRepositoryPort
from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.application.services.incident_service import IncidentService
from app.application.services.technician_service import TechnicianService
from app.domain.entities.incident import Incident

router = APIRouter()


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


_repository: IncidentRepositoryPort | None = None


def get_incident_service() -> IncidentService:
    """Obtiene el servicio de incidentes con repositorio SQL y categorías.

    El repositorio se cachea en módulo; ``_repository = None`` en tests lo reinicia.
    """
    global _repository
    from app.infrastructure.adapters.incident_category_repository import (
        SqlAlchemyIncidentCategoryRepository,
    )
    from app.infrastructure.adapters.sql_incident_repository import (
        SqlIncidentRepository,
    )

    if _repository is None:
        _repository = SqlIncidentRepository()
    return IncidentService(
        repository=_repository,
        category_repository=SqlAlchemyIncidentCategoryRepository(),
    )


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
        "estado": "status",
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
) -> PaginatedAdminIncidentsResponse:
    """Bandeja del administrador: lista paginada de todos los incidentes,
    ordenados del más reciente al más antiguo (ordenamiento en base de datos)."""
    service = get_incident_service()
    incidents = service.list_incidents()
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
) -> PaginatedIncidentsResponse:
    service = get_incident_service()
    incidents = service.list_incidents()
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
    response_model=IncidentResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_incident(incident_id: UUID) -> IncidentResponse:
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
    return _incident_to_response(incident)


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
) -> IncidentResponse:
    """Asocia un técnico activo con rol adecuado a un incidente existente."""
    incident = technician_service.assign_technician_to_incident(
        incident_id=incident_id,
        technician_id=payload.tecnico_id,
    )
    return _incident_to_response(incident)


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
)
async def upload_incident_evidence(
    incident_id: UUID,
    photo: UploadFile = File(...),
    evidence_service: IncidentEvidenceService = Depends(get_incident_evidence_service),
) -> IncidentEvidenceUploadResponse:
    """Valida y carga una evidencia fotográfica para un incidente."""
    stored_file = await evidence_service.upload_evidence(
        incident_id=incident_id,
        file=photo,
    )

    return IncidentEvidenceUploadResponse(
        incident_id=incident_id,
        filename=photo.filename or "",
        content_type=(photo.content_type or "").lower(),
        storage_object_name=stored_file.object_name,
        file_url=stored_file.file_url,
        message="Evidencia fotográfica cargada correctamente",
    )
