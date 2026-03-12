"""Script de utilidad para crear usuarios de prueba en la base de datos.

Este script NO es una migración, sino una herramienta de desarrollo
para poblar la BD con datos de prueba.

Uso:
    python -m app.scripts.seed_users
"""

from collections.abc import Sequence
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.infrastructure.database.models import RoleModel, UserModel


def ensure_role(
    db,
    *,
    name: str,
    description: str,
) -> tuple[RoleModel, bool]:
    """Crea el rol si no existe y devuelve si fue creado."""
    stmt = select(RoleModel).where(RoleModel.name == name)
    existing_role = db.scalar(stmt)

    if existing_role:
        return existing_role, False

    role = RoleModel(
        id=uuid4(),
        name=name,
        description=description,
    )
    db.add(role)
    db.flush()
    return role, True


def ensure_user(
    db,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    role_id,
) -> tuple[UserModel, bool]:
    """Crea el usuario si no existe y devuelve si fue creado."""
    stmt = select(UserModel).where(UserModel.email == email)
    existing_user = db.scalar(stmt)

    if existing_user:
        return existing_user, False

    user = UserModel(
        id=uuid4(),
        first_name=first_name,
        last_name=last_name,
        email=email,
        password_hash=hash_password(password),
        role_id=role_id,
        is_active=True,
    )
    db.add(user)
    return user, True


def seed_users() -> None:
    """Crea usuarios y roles de prueba en la base de datos."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("Verificando roles...")
        admin_role, admin_role_created = ensure_role(
            db,
            name="Administrator",
            description="Administrador del sistema",
        )
        student_role, student_role_created = ensure_role(
            db,
            name="Student",
            description="Estudiante",
        )
        technician_role, technician_role_created = ensure_role(
            db,
            name="Technician",
            description="Técnico de mantenimiento",
        )

        if admin_role_created or student_role_created or technician_role_created:
            db.commit()
            print("✓ Roles creados o completados")
        else:
            print("Roles ya existen")

        print("\nVerificando usuarios de prueba...")
        users_to_seed: Sequence[dict[str, str]] = (
            {
                "first_name": "Admin",
                "last_name": "Sistema",
                "email": "admin@usbcali.edu.co",
                "password": "admin123",
                "role_id": admin_role.id,
            },
            {
                "first_name": "Juan",
                "last_name": "Pérez",
                "email": "estudiante@correo.usbcali.edu.co",
                "password": "estudiante123",
                "role_id": student_role.id,
            },
            {
                "first_name": "María",
                "last_name": "García",
                "email": "tecnico@usbcali.edu.co",
                "password": "tecnico123",
                "role_id": technician_role.id,
            },
        )
        created_users: list[tuple[str, str]] = []

        for user_data in users_to_seed:
            _, created = ensure_user(db, **user_data)
            if created:
                created_users.append((user_data["email"], user_data["password"]))

        if created_users:
            db.commit()
            print("✓ Usuarios creados exitosamente")
        else:
            print("Usuarios de prueba ya existen en la BD")

        print("\nCredenciales de prueba:")
        print("-" * 50)
        print("Administrador:")
        print("  Email: admin@usbcali.edu.co")
        print("  Password: admin123")
        print("\nEstudiante:")
        print("  Email: estudiante@correo.usbcali.edu.co")
        print("  Password: estudiante123")
        print("\nTécnico:")
        print("  Email: tecnico@usbcali.edu.co")
        print("  Password: tecnico123")
        print("-" * 50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Poblando base de datos con usuarios de prueba...")
    print("=" * 50)
    seed_users()
    print("\n✅ Proceso completado")
