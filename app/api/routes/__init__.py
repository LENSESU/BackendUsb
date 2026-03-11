from fastapi import APIRouter

from app.api.routes import auth, incident_category, items

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(incident_category.router)