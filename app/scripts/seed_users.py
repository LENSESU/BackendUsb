"""Script de utilidad para crear usuarios de prueba en la base de datos.

Este script NO es una migración, sino una herramienta de desarrollo
para poblar la BD con datos de prueba.

Uso:
    python -m app.scripts.seed_users
"""

from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.infrastructure.database.models import RoleModel, UserModel


def seed_users() -> None:
    """Crea usuarios y roles de prueba en la base de datos."""
    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Verificar si ya existen roles
        stmt = select(RoleModel).where(RoleModel.name == "Administrator")
        admin_role = db.scalar(stmt)

        # Crear roles si no existen
        if not admin_role:
            print("Creando roles...")
            admin_role = RoleModel(
                id=uuid4(),
                name="Administrator",
                description="Administrador del sistema",
            )
            student_role = RoleModel(
                id=uuid4(),
                name="Student",
                description="Estudiante",
            )
            technician_role = RoleModel(
                id=uuid4(),
                name="Technician",
                description="Técnico de mantenimiento",
            )
            db.add_all([admin_role, student_role, technician_role])
            db.commit()
            db.refresh(admin_role)
            db.refresh(student_role)
            db.refresh(technician_role)
            print(f"✓ Roles creados")
        else:
            print("Roles ya existen")
            stmt = select(RoleModel).where(RoleModel.name == "Student")
            student_role = db.scalar(stmt)
            stmt = select(RoleModel).where(RoleModel.name == "Technician")
            technician_role = db.scalar(stmt)

        # Verificar si ya existe el usuario de prueba
        stmt = select(UserModel).where(UserModel.email == "admin@usb.ve")
        existing_user = db.scalar(stmt)

        if not existing_user:
            print("\nCreando usuarios de prueba...")

            # Usuario administrador
            admin_user = UserModel(
                id=uuid4(),
                first_name="Admin",
                last_name="Sistema",
                email="admin@usb.ve",
                password_hash=hash_password("admin123"),
                role_id=admin_role.id,
                is_active=True,
            )

            # Usuario estudiante
            student_user = UserModel(
                id=uuid4(),
                first_name="Juan",
                last_name="Pérez",
                email="estudiante@usb.ve",
                password_hash=hash_password("estudiante123"),
                role_id=student_role.id,
                is_active=True,
            )

            # Usuario técnico
            tech_user = UserModel(
                id=uuid4(),
                first_name="María",
                last_name="García",
                email="tecnico@usb.ve",
                password_hash=hash_password("tecnico123"),
                role_id=technician_role.id,
                is_active=True,
            )

            db.add_all([admin_user, student_user, tech_user])
            db.commit()

            print("✓ Usuarios creados exitosamente\n")
            print("Credenciales de prueba:")
            print("-" * 50)
            print("Administrador:")
            print("  Email: admin@usb.ve")
            print("  Password: admin123")
            print("\nEstudiante:")
            print("  Email: estudiante@usb.ve")
            print("  Password: estudiante123")
            print("\nTécnico:")
            print("  Email: tecnico@usb.ve")
            print("  Password: tecnico123")
            print("-" * 50)
        else:
            print("\nUsuarios de prueba ya existen en la BD")
            print("\nCredenciales de prueba:")
            print("-" * 50)
            print("Email: admin@usb.ve | Password: admin123")
            print("Email: estudiante@usb.ve | Password: estudiante123")
            print("Email: tecnico@usb.ve | Password: tecnico123")
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
