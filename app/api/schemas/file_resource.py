"""Esquemas Pydantic para archivos."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class FileResourceCreate(BaseModel):
    """Payload para registrar un archivo."""

    url: HttpUrl
    file_type: str | None = Field(default=None, max_length=50)
    uploaded_by_user_id: int | None = Field(default=None, ge=1)


class FileResourceResponse(BaseModel):
    """Respuesta con datos de un archivo."""

    id: int
    url: HttpUrl
    file_type: str | None = None
    uploaded_by_user_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

