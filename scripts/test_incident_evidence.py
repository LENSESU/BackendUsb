#!/usr/bin/env python3
"""
Script para probar el endpoint POST /api/v1/incidents/{incident_id}/evidence.

Opciones:
  1) Generar datos de prueba (rol, usuario, categoría, foto "antes", incidente)
     y luego subir una evidencia de prueba al endpoint.
  2) Llamar al endpoint con un incident_id y una imagen existentes.

Uso:
  # Generar datos y probar (API en http://localhost:8000)
  python scripts/test_incident_evidence.py

  # Solo crear un incidente y mostrar su UUID para probar en Swagger
  python scripts/test_incident_evidence.py --seed-only

  # Llamar al endpoint con incidente e imagen existentes
  python scripts/test_incident_evidence.py --incident-id UUID --image ruta/imagen.jpg

  # Especificar URL base de la API
  python scripts/test_incident_evidence.py --base-url http://localhost:8001
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Añadir raíz del proyecto al path para importar app
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Imagen JPEG mínima válida (1x1 píxel) para pruebas sin archivo externo
# Fuente: minimal JPEG binary para tests
_MINIMAL_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
    b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
    b"\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.34\xff\xc0\x00\x0b"
    b"\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01"
    b"\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00"
    b"\x00\x00?\x00\xfe\x02\x0e\xff\xd9"
)


def _create_test_data() -> str:
    """Crea datos mínimos para pruebas y retorna el incident_id."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings
    from app.core.security import hash_password
    from app.infrastructure.database.models import (
        FileModel,
        IncidentCategoryModel,
        IncidentModel,
        RoleModel,
        UserModel,
    )

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Rol Student
        stmt = select(RoleModel).where(RoleModel.name == "Student")
        student_role = db.scalar(stmt)
        if not student_role:
            student_role = RoleModel(name="Student", description="Estudiante")
            db.add(student_role)
            db.commit()
            db.refresh(student_role)

        # Usuario estudiante para el incidente
        stmt = select(UserModel).where(UserModel.email == "estudiante@usb.ve")
        student = db.scalar(stmt)
        if not student:
            student = UserModel(
                first_name="Juan",
                last_name="Pérez",
                email="estudiante@usb.ve",
                password_hash=hash_password("estudiante123"),
                role_id=student_role.id,
                is_active=True,
            )
            db.add(student)
            db.commit()
            db.refresh(student)

        # Categoría de incidente
        stmt = select(IncidentCategoryModel).where(
            IncidentCategoryModel.name == "Prueba script"
        )
        category = db.scalar(stmt)
        if not category:
            category = IncidentCategoryModel(
                name="Prueba script",
                description="Categoría para tests del script de evidencia",
            )
            db.add(category)
            db.commit()
            db.refresh(category)

        # Foto "antes" (placeholder para poder crear el incidente)
        before_file = FileModel(
            url="https://placeholder.local/antes.jpg",
            file_type="image/jpeg",
            uploaded_by_user_id=student.id,
        )
        db.add(before_file)
        db.commit()
        db.refresh(before_file)

        # Incidente
        incident = IncidentModel(
            student_id=student.id,
            technician_id=None,
            category_id=category.id,
            description="Incidente de prueba creado por test_incident_evidence.py",
            campus_place=None,
            latitude=None,
            longitude=None,
            status="New",
            priority=None,
            before_photo_id=before_file.id,
            after_photo_id=None,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)

        return str(incident.id)
    except Exception as e:
        db.rollback()
        raise RuntimeError(f"Error creando datos de prueba: {e}") from e
    finally:
        db.close()


def _upload_evidence(
    base_url: str,
    incident_id: str,
    image_path: Path | None,
    use_minimal_jpeg: bool,
) -> None:
    """Llama al endpoint POST /api/v1/incidents/{incident_id}/evidence."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v1/incidents/{incident_id}/evidence"

    if image_path is not None:
        if not image_path.is_file():
            raise FileNotFoundError(f"No existe el archivo: {image_path}")
        file_obj = open(image_path, "rb")
        filename = image_path.name
        content_type = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            content_type = "image/png"
        files = {"photo": (filename, file_obj, content_type)}
        try:
            resp = httpx.post(url, files=files, timeout=30.0)
        finally:
            file_obj.close()
    elif use_minimal_jpeg:
        files = {"photo": ("evidencia_test.jpg", _MINIMAL_JPEG, "image/jpeg")}
        resp = httpx.post(url, files=files, timeout=30.0)
    else:
        raise ValueError(
            "Indica --image RUTA para la imagen a subir, o ejecuta sin --incident-id "
            "para generar datos y usar una imagen mínima de prueba."
        )

    print(f"Status: {resp.status_code}")
    print(resp.text)
    if resp.status_code != 201:
        sys.exit(1)
    try:
        data = resp.json()
        print("\nRespuesta:")
        for k, v in data.items():
            print(f"  {k}: {v}")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prueba el endpoint de carga de evidencia de incidentes."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL base de la API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--incident-id",
        help="UUID del incidente. Si no se pasa, se crean datos de prueba en la BD.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        help=(
            "Ruta a la imagen (JPEG/PNG) a subir. "
            "Si no se pasa y se generan datos, se usa una imagen mínima."
        ),
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help=(
            "Solo crea datos de prueba en la BD y muestra el incident_id "
            "para usar en Swagger."
        ),
    )
    args = parser.parse_args()

    if args.seed_only:
        print(
            "Creando datos de prueba en la BD (rol, usuario, categoría, incidente)..."
        )
        incident_id = _create_test_data()
        print("\n✅ Incidente creado. Usa este UUID en Swagger:")
        print(f"   {incident_id}")
        print(f"\n   Swagger UI: {args.base_url.rstrip('/')}/docs")
        print(
            "   Endpoint: POST /api/v1/incidents/{incident_id}/evidence → "
            "pega el UUID arriba como incident_id."
        )
        return

    if args.incident_id and args.image is None:
        parser.error("Con --incident-id debes indicar --image RUTA.")

    if args.incident_id:
        incident_id = args.incident_id
        print(f"Usando incident_id existente: {incident_id}")
    else:
        print(
            "Creando datos de prueba en la BD (rol, usuario, categoría, incidente)..."
        )
        incident_id = _create_test_data()
        print(f"Incidente creado: {incident_id}")

    use_minimal = args.image is None

    print(f"\nLlamando a POST {args.base_url}/api/v1/incidents/{incident_id}/evidence")
    _upload_evidence(
        base_url=args.base_url,
        incident_id=incident_id,
        image_path=args.image,
        use_minimal_jpeg=use_minimal,
    )
    print("\n✅ Prueba completada.")


if __name__ == "__main__":
    main()
