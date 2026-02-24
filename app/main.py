"""Punto de entrada de la aplicación FastAPI."""

from fastapi import FastAPI

from app.api.routes import api_router

app = FastAPI(
    title="Backend API",
    description="API con arquitectura hexagonal",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de que el servicio está vivo."""
    return {"status": "ok"}
