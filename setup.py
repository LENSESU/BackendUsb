"""
Script de inicio rápido para configurar el proyecto.

Ejecuta este script después de clonar el repositorio para:
1. Instalar dependencias
2. Crear usuarios de prueba en la base de datos
"""

import subprocess
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{'=' * 60}")
    print(f"📌 {description}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(e.stderr)
        return False


def main():
    """Ejecuta el setup inicial del proyecto."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║         Backend USB - Setup Inicial                    ║
    ║         Sistema de Autenticación con JWT               ║
    ╚════════════════════════════════════════════════════════╝
    """)

    # Verificar que existe .env
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("⚠️  No se encontró archivo .env")
        print("📝 Copiando .env.example a .env...")
        env_example.read_text().replace("XXX", "XXX")  # Trigger copy
        with open(".env", "w") as f:
            f.write(env_example.read_text())
        print("✅ Archivo .env creado")
    
    # Instalar dependencias
    if not run_command(
        "pip install -r requirements.txt",
        "Instalando dependencias de Python"
    ):
        print("\n❌ Error instalando dependencias")
        return

    print("\n")
    print("📊 Setup completado!")
    print("\nPróximos pasos:")
    print("-" * 60)
    print("1. Asegúrate de que PostgreSQL esté corriendo")
    print("2. Configura las variables en .env si es necesario")
    print("3. Ejecuta: uvicorn app.main:app --reload")
    print("4. Crea usuarios de prueba: python -m app.scripts.seed_users")
    print("5. Visita: http://127.0.0.1:8000/docs")
    print("-" * 60)
    print("\n🔐 Endpoints de Autenticación:")
    print("   POST /api/v1/auth/login  - Iniciar sesión")
    print("   POST /api/v1/auth/logout - Cerrar sesión")
    print("   GET  /api/v1/auth/me     - Info usuario actual")
    print("-" * 60)


if __name__ == "__main__":
    main()
