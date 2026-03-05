"""Dependencias compartidas de la API."""

from app.api.dependencies.auth import get_current_token, get_current_user_id

__all__ = ["get_current_token", "get_current_user_id"]
