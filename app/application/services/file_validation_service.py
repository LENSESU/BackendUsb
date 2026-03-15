"""Servicio de aplicación para validar archivos subidos."""

from pathlib import Path

from fastapi import HTTPException, UploadFile, status


class FileValidationService:
    """Valida formato de archivos de evidencia fotográfica."""

    _allowed_content_types = {"image/jpeg", "image/png"}
    _allowed_extensions = {".jpg", ".jpeg", ".png"}
    _max_file_size_bytes = 5 * 1024 * 1024  # 5MB

    @classmethod
    async def validate_incident_evidence_image(cls, file: UploadFile) -> None:
        """Valida que la evidencia sea una imagen JPEG o PNG con tamaño <= 5MB."""
        filename = (file.filename or "").strip()
        extension = Path(filename).suffix.lower()
        content_type = (file.content_type or "").lower()

        if content_type not in cls._allowed_content_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Formato de archivo no permitido. Solo se aceptan JPG, JPEG o PNG."
                ),
            )

        if extension not in cls._allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Extensión de archivo no permitida. "
                    "Solo se aceptan .jpg, .jpeg o .png."
                ),
            )

        # Validar tamaño del archivo
        contents = await file.read()
        file_size = len(contents)
        await file.seek(0)  # Volver al inicio para uso posterior

        if file_size > cls._max_file_size_bytes:
            size_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "El archivo supera el tamaño máximo permitido de 5MB. "
                    f"Tamaño recibido: {size_mb:.2f}MB."
                ),
            )
