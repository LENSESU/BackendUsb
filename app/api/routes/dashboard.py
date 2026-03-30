"""Ruta consolidada para dashboard del estudiante."""

import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.dependencies.auth import require_role
from app.api.dependencies.incident_category import get_incident_category_service
from app.api.dependencies.suggestion import get_suggestion_service
from app.api.routes.auth import get_current_user_info
from app.api.routes.incidents import get_incident_service
from app.api.schemas.dashboard import (
    DashboardIncident,
    DashboardResponse,
    DashboardSuggestion,
    DashboardUser,
)
from app.application.services.incident_category_service import IncidentCategoryService
from app.application.services.suggestion_service import SuggestionService

router = APIRouter()


@router.get(
    "/",
    response_model=DashboardResponse,
    dependencies=[Depends(require_role("Administrator", "Student", "Technician"))],
)
async def get_dashboard(
    current_user: dict = Depends(get_current_user_info),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
    incident_category_service: IncidentCategoryService = Depends(
        get_incident_category_service
    ),
) -> DashboardResponse:
    """Retorna información consolidada para el dashboard."""
    try:
        user_id = UUID(str(current_user.get("user_id")))
        incident_service = get_incident_service()

        user_task = asyncio.to_thread(DashboardUser.model_validate, current_user)
        incidents_task = asyncio.to_thread(
            incident_service.get_recent_incidents, user_id, 5
        )
        suggestions_task = asyncio.to_thread(suggestion_service.get_top_suggestions, 5)

        user, incidents, suggestions = await asyncio.gather(
            user_task,
            incidents_task,
            suggestions_task,
        )

        filtered_incidents = [
            i for i in incidents if i.created_at is not None and i.id is not None
        ]
        category_tasks = [
            asyncio.to_thread(incident_category_service.get_by_id, str(i.category_id))
            for i in filtered_incidents
        ]
        categories = await asyncio.gather(*category_tasks) if category_tasks else []

        return DashboardResponse(
            user=user,
            recentIncidents=[
                DashboardIncident(
                    id=i.id,
                    category_id=i.category_id,
                    categoria=(categories[idx].name if categories[idx] else None),
                    description=i.description,
                    status=i.status,
                    priority=i.priority,
                    created_at=i.created_at,
                )
                for idx, i in enumerate(filtered_incidents)
            ],
            suggestions=[
                DashboardSuggestion(
                    id=s.id,
                    titulo=s.title,
                    total_votos=s.total_votes,
                )
                for s in suggestions
                if s.id is not None
            ],
        )
    except HTTPException:
        raise
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": True, "message": "Error interno del servidor"},
        )
