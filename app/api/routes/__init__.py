from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    incident_category,
    incidents,
    items,
    suggestions,
    technicians,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(
    technicians.router, prefix="/technicians", tags=["technicians"]
)
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(
    incident_category.router, prefix="/categories", tags=["categories"]
)
api_router.include_router(
    suggestions.router, prefix="/suggestions", tags=["suggestions"]
)
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
