"""Script sencillo para crear un incidente de prueba y mostrar su UUID.

Uso:
    python -m app.scripts.create_incident_for_evidence

Requisitos:
    - Variables de entorno de base de datos configuradas (.env).
    - Migraciones aplicadas (tablas creadas).
    - Al menos un usuario y una categoría de incidente ya existentes
      (por ejemplo, creados con los scripts de seed).

El script:
 1. Toma el primer usuario y la primera categoría existentes en la BD.
 2. Crea un incidente mínimo usando SqlIncidentRepository.
 3. Imprime por consola el UUID del incidente creado.
 4. Con ese UUID puedes llamar luego al endpoint:
        POST /api/v1/incidents/{incident_id}/evidence
    desde Postman, Thunder Client o tu frontend.
"""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.application.services.incident_service import IncidentService
from app.core.config import settings
from app.infrastructure.adapters.sql_incident_repository import SqlIncidentRepository
from app.infrastructure.database.models import IncidentCategoryModel, UserModel


def _get_session() -> Session:
    """Crea una sesión síncrona nueva."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def main() -> None:
    """Crea un incidente mínimo con FK válidas y muestra su ID por consola."""
    db = _get_session()
    try:
        user = db.scalar(select(UserModel).limit(1))
        category = db.scalar(select(IncidentCategoryModel).limit(1))

        if user is None or category is None:
            print(
                "No se encontró al menos un usuario y una categoría en la base "
                "de datos.\nEjecuta primero los scripts de seed para poblar las "
                "tablas users e incident_categories."
            )
            return

        repository = SqlIncidentRepository()
        service = IncidentService(repository=repository)

        incident = service.create_incident(
            student_id=user.id,
            category_id=category.id,
            description="Incidente de prueba para carga de evidencia",
        )
    finally:
        db.close()

    print("Incidente de prueba creado.")
    print(f"ID del incidente: {incident.id}")


if __name__ == "__main__":
    main()

