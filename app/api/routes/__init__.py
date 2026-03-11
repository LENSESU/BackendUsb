from fastapi import APIRouter
from app.api.routes import auth, incidents, items, incident_category

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
api_router.include_router(incident_category.router)