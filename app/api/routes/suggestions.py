"""Rutas HTTP para sugerencias."""

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)

from app.api.dependencies.auth import (
    get_current_user_id,
    require_role,
)
from app.api.dependencies.storage import (
    get_file_repository,
    get_incident_evidence_service,
)
from app.api.dependencies.suggestion import get_suggestion_service
from app.api.schemas.suggestion import (
    PaginatedPopularSuggestionsResponse,
    PaginatedSuggestionsResponse,
    SuggestionPopularResponse,
    SuggestionResponse,
    SuggestionUpdate,
)
from app.application.ports.file_repository import FileRepositoryPort
from app.application.services.incident_evidence_service import IncidentEvidenceService
from app.application.services.suggestion_service import SuggestionService
from app.domain.entities.suggestion import Suggestion

router = APIRouter()


def _to_response(s: Suggestion, photo_url: str | None = None) -> SuggestionResponse:
    if s.id is None or s.created_at is None:
        msg = "La sugerencia persistida debe tener id y created_at"
        raise RuntimeError(msg)
    return SuggestionResponse(
        id=s.id,
        estudiante_id=s.student_id,
        titulo=s.title,
        contenido=s.content,
        total_votos=s.total_votes,
        foto_url=photo_url,
        comentario_institucional=s.institutional_comment,
        created_at=s.created_at,
        etiquetas=s.tags or [],
    )


def _to_popular_response(s: Suggestion) -> SuggestionPopularResponse:
    if s.id is None:
        msg = "La sugerencia persistida debe tener id"
        raise RuntimeError(msg)
    return SuggestionPopularResponse(
        id=s.id,
        titulo=s.title,
        total_votos=s.total_votes,
    )


@router.get(
    "/",
    response_model=PaginatedSuggestionsResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_suggestions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    service: SuggestionService = Depends(get_suggestion_service),
    file_repository: FileRepositoryPort = Depends(get_file_repository),
) -> PaginatedSuggestionsResponse:
    suggestions = service.list_all()
    total = len(suggestions)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit

    # Convertir sugerencias a respuestas con URLs
    items = []
    for s in suggestions[start:end]:
        photo_url = None
        if s.photo_id:
            photo_url = file_repository.get_by_id(s.photo_id)
        items.append(_to_response(s, photo_url=photo_url))

    return PaginatedSuggestionsResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/me",
    response_model=PaginatedSuggestionsResponse,
    dependencies=[Depends(require_role("Student"))],
)
def list_my_suggestions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    current_user_id: UUID = Depends(get_current_user_id),
    service: SuggestionService = Depends(get_suggestion_service),
) -> PaginatedSuggestionsResponse:
    suggestions = service.list_by_student(current_user_id)
    total = len(suggestions)
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    return PaginatedSuggestionsResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=[_to_response(s) for s in suggestions[start:end]],
    )


@router.get(
    "/popular",
    response_model=PaginatedPopularSuggestionsResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def list_popular_suggestions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    service: SuggestionService = Depends(get_suggestion_service),
) -> PaginatedPopularSuggestionsResponse:
    total = len(service.list_all())
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    upto = page * limit
    suggestions = service.list_popular(limit=upto)
    start = (page - 1) * limit
    end = start + limit
    return PaginatedPopularSuggestionsResponse(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        items=[_to_popular_response(s) for s in suggestions[start:end]],
    )


@router.get(
    "/{suggestion_id}",
    response_model=SuggestionResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def get_suggestion(
    suggestion_id: UUID,
    service: SuggestionService = Depends(get_suggestion_service),
    file_repository: FileRepositoryPort = Depends(get_file_repository),
) -> SuggestionResponse:
    suggestion = service.get_by_id(suggestion_id)
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Sugerencia no encontrada",
                "error_code": "SUGGESTION_NOT_FOUND",
            },
        )
    # Obtener URL de la foto si existe
    photo_url = None
    if suggestion.photo_id:
        photo_url = file_repository.get_by_id(suggestion.photo_id)
    return _to_response(suggestion, photo_url=photo_url)


@router.post(
    "/",
    response_model=SuggestionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
async def create_suggestion(
    current_user_id: UUID = Depends(get_current_user_id),
    service: SuggestionService = Depends(get_suggestion_service),
    evidence_service: IncidentEvidenceService = Depends(get_incident_evidence_service),
    file_repository: FileRepositoryPort = Depends(get_file_repository),
    titulo: str = Form(
        ...,
        min_length=1,
        max_length=200,
        description="Título de la sugerencia (máx 200 caracteres)",
    ),
    contenido: str = Form(
        ..., min_length=1, description="Contenido/descripción de la sugerencia"
    ),
    etiquetas: str | None = Form(
        None,
        description="Etiquetas separadas por coma (ej: 'infraestructura, seguridad')",
    ),
    photo: UploadFile | None = File(
        None, description="Imagen adjunta (opcional) - Formatos: JPEG, PNG. Máximo 5MB"
    ),
) -> SuggestionResponse:
    """Crea una nueva sugerencia con texto, etiquetas opcionales y foto opcional.

    **Parámetros (multipart/form-data):**
    - `titulo`: Título de la sugerencia (1-200 caracteres)
    - `contenido`: Descripción detallada de la sugerencia
    - `etiquetas`: Lista de etiquetas separadas por coma (ej: 'infraestructura,
    seguridad,tecnología')
    - `photo`: Archivo de imagen (opcional) - Solo JPEG y PNG, máximo 5MB

    **Flujo interno:**
    1. Procesar etiquetas desde string separado por comas
    2. Crear sugerencia sin foto (para obtener ID)
    3. Si hay foto, cargarla a Google Cloud Storage en carpeta:
    `suggestions/{suggestion_id}`
    4. Actualizar sugerencia con el `photo_id`

    **Respuesta:**
    - Retorna la sugerencia creada con todos sus datos incluidas etiquetas asociadas
    """
    # Procesar etiquetas
    tag_list = []
    if etiquetas:
        tag_list = [t.strip() for t in etiquetas.split(",") if t.strip()]

    # Crear sugerencia SIN foto primero (necesitamos el ID para la carpeta en GCS)
    try:
        suggestion = service.create(
            student_id=current_user_id,
            title=titulo,
            content=contenido,
            tags=tag_list if tag_list else None,
            photo_id=None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(e),
                "error_code": "SUGGESTION_VALIDATION_ERROR",
            },
        ) from e

    if suggestion.id is None:
        raise RuntimeError("La sugerencia creada debe tener un ID")

    # Si hay foto, cargarla ahora usando el ID de la sugerencia
    if photo:
        try:
            file_id, file_url = await evidence_service.upload_file_with_validation(
                prefix=f"suggestions/{suggestion.id}",
                file=photo,
            )

            # Actualizar la sugerencia con el photo_id
            suggestion = service.update(
                suggestion_id=suggestion.id,
                partial={"foto_id": file_id},
            )
            if suggestion is None:
                raise RuntimeError("No se pudo actualizar la sugerencia con la foto")

        except HTTPException:
            # Re-lanzar errores HTTP del servicio de almacenamiento
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": f"Error al procesar la foto: {str(e)}",
                    "error_code": "SUGGESTION_PHOTO_ERROR",
                },
            ) from e

    # Obtener URL de la foto si existe
    photo_url = None
    if suggestion.photo_id:
        photo_url = file_repository.get_by_id(suggestion.photo_id)

    return _to_response(suggestion, photo_url=photo_url)


@router.patch(
    "/{suggestion_id}",
    response_model=SuggestionResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def update_suggestion(
    suggestion_id: UUID,
    payload: SuggestionUpdate,
    service: SuggestionService = Depends(get_suggestion_service),
    file_repository: FileRepositoryPort = Depends(get_file_repository),
) -> SuggestionResponse:
    """Actualiza los campos textuales de una sugerencia.

    **Parámetros (application/json):**
    - `titulo`: Nuevo título (opcional, 1-200 caracteres)
    - `contenido`: Nuevo contenido (opcional, mínimo 1 carácter)
    - `comentario_institucional`: Respuesta del administrador (opcional)
    - `total_votos`: Número de votos (opcional, no negativo)

    **Nota:** Para actualizar la foto, usa el endpoint específico:
    `PATCH /api/v1/suggestions/{suggestion_id}/photo`
    """
    partial = payload.model_dump(exclude_unset=True)
    try:
        suggestion = service.update(suggestion_id, partial)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": str(e),
                "error_code": "SUGGESTION_VALIDATION_ERROR",
            },
        ) from e
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Sugerencia no encontrada",
                "error_code": "SUGGESTION_NOT_FOUND",
            },
        )
    # Obtener URL de la foto si existe
    photo_url = None
    if suggestion.photo_id:
        photo_url = file_repository.get_by_id(suggestion.photo_id)
    return _to_response(suggestion, photo_url=photo_url)


@router.patch(
    "/{suggestion_id}/photo",
    response_model=SuggestionResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
async def update_suggestion_photo(
    suggestion_id: UUID,
    photo: UploadFile = File(
        ..., description="Imagen a reemplazar - Formatos: JPEG, PNG. Máximo 5MB"
    ),
    service: SuggestionService = Depends(get_suggestion_service),
    evidence_service: IncidentEvidenceService = Depends(get_incident_evidence_service),
    file_repository: FileRepositoryPort = Depends(get_file_repository),
) -> SuggestionResponse:
    """Actualiza SOLO la foto de una sugerencia existente.

    **Parámetros (multipart/form-data):**
    - `photo`: Archivo JPEG o PNG (máximo 5MB)

    **Flujo:**
    1. Valida que la sugerencia exista
    2. Valida la nueva foto (JPEG/PNG, max 5MB)
    3. Carga la foto a Google Cloud Storage
    4. Reemplaza la foto anterior con la nueva
    5. Retorna la sugerencia actualizada con nueva `foto_url`

    **Nota:** Para actualizar campos de texto, usa:
    `PATCH /api/v1/suggestions/{suggestion_id}`
    """
    # Verificar que la sugerencia existe
    suggestion = service.get_by_id(suggestion_id)
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Sugerencia no encontrada",
                "error_code": "SUGGESTION_NOT_FOUND",
            },
        )

    # Cargar la nueva foto
    try:
        file_id, file_url = await evidence_service.upload_file_with_validation(
            prefix=f"suggestions/{suggestion_id}",
            file=photo,
        )

        # Actualizar la sugerencia con el nuevo photo_id
        suggestion = service.update(
            suggestion_id=suggestion_id,
            partial={"foto_id": file_id},
        )
        if suggestion is None:
            raise RuntimeError("No se pudo actualizar la sugerencia con la foto")

    except HTTPException:
        # Re-lanzar errores HTTP del servicio de almacenamiento
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": f"Error al procesar la foto: {str(e)}",
                "error_code": "SUGGESTION_PHOTO_ERROR",
            },
        ) from e

    # Obtener URL de la foto actualizada
    photo_url = file_repository.get_by_id(file_id) if file_id else None

    return _to_response(suggestion, photo_url=photo_url)


@router.delete(
    "/{suggestion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
def delete_suggestion(
    suggestion_id: UUID,
    service: SuggestionService = Depends(get_suggestion_service),
) -> None:
    deleted = service.delete(suggestion_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "Sugerencia no encontrada",
                "error_code": "SUGGESTION_NOT_FOUND",
            },
        )
