# Backend - FastAPI con Arquitectura Hexagonal

API REST construida con **FastAPI** y una estructura básica en **arquitectura hexagonal** (puertos y adaptadores).

## Estructura del proyecto

```
app/
├── domain/              # Núcleo: entidades y reglas de negocio
│   └── entities/
├── application/         # Casos de uso y puertos (interfaces)
│   ├── ports/
│   └── services/
├── infrastructure/      # Adaptadores: persistencia, APIs externas
│   └── adapters/
├── api/                 # Capa de presentación (HTTP)
│   ├── routes/
│   └── schemas/
└── main.py
```

- **Domain**: entidades puras, sin dependencias de frameworks.
- **Application**: define contratos (puertos) y orquesta los casos de uso.
- **Infrastructure**: implementa los puertos (por ejemplo, repositorio en memoria o base de datos).
- **API**: rutas FastAPI y DTOs (schemas Pydantic).

## Requisitos

- Python 3.11+

## Clonar el repositorio y ejecutar el proyecto

Clona el repositorio :

```bash
git clone https://github.com/Chologalactico/BackendUsb.git
```
Crea una una nueva rama
```bash
git checkout -b dev
```
Todo se sube a la rama que creaste, para ya luego hacer un PR a la rama DEV 

-⚠️ Peligroso. Hacer algun push a la rama main o develop 

Entra al directorio del proyecto:

```bash
cd BackendUsb
```

Crea el entorno virtual:

```bash
python -m venv .venv
```

Activa el entorno virtual.

En Windows (PowerShell o CMD):

```bash
.venv\Scripts\activate
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

Ejecuta la aplicación:

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000`.

### Ejecutar tests

Los tests están en `tests/` (por ejemplo `tests/test_health.py`, que prueba el endpoint `/health`). Desde la raíz del proyecto (donde están `app/` y `tests/`):

```bash
python -m pytest
```

### CI/CD (GitHub Actions)

Este repositorio incluye un workflow de CI en `.github/workflows/ci.yml` que se ejecuta en:

- Push a la rama `dev`.
- Pull requests hacia `dev` y `main`.

**Es obligatorio que todos los checks de GitHub Actions pasen en verde** antes de fusionar un PR. Revisa la pestaña **Actions** en el repositorio y el estado de los checks en cada Pull Request; si algo falla, corrige el código y vuelve a subir.

El pipeline realiza:

- **Linting con Ruff** sobre la carpeta `app/`.
- **Chequeo de formato** con `ruff format --check app`.
- **Chequeo básico de sintaxis** con `python -m compileall app`.
- **Tests** con `pytest` (incluye `tests/test_health.py`).

#### Comandos locales (verificar antes de subir)

Para reproducir en tu máquina lo que hace el CI y evitar fallos en Actions:

```bash
# Linter: solo revisar
python -m ruff check app

# Linter: revisar y aplicar correcciones automáticas
python -m ruff check app --fix

# Formato: comprobar que el código está formateado
python -m ruff format --check app

# Formato: aplicar formato automáticamente
python -m ruff format app
```

Para hacer obligatorio el pipeline antes de fusionar PRs, configura en GitHub:

1. `Settings` → `Branches` → `Branch protection rules`.
2. Protege `dev` y `main`.
3. Añade el check de estado del workflow de CI como requerido.

### Ejecución con Docker

Requisitos: [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/).

Construir y levantar los servicios (backend + PostgreSQL):

```bash
docker compose up --build
```

Para ejecutar en segundo plano:

```bash
docker compose up -d --build
```

Crea un archivo `.env` en la raíz para configurar Postgres:

```bash
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=app_db
```

Con Docker, la API queda en `http://127.0.0.1:8000` y PostgreSQL en `localhost:5432` (usuario/contraseña/base según `.env` o valores por defecto anteriores).

### Migraciones (Alembic)

**No tienes que hacer nada a mano.** Al arrancar la app (con Postgres corriendo), se aplican solas las migraciones: se crean o actualizan las tablas en la base de datos. Solo asegúrate de tener Postgres levantado y las variables de entorno (`POSTGRES_*` o `DATABASE_URL`) en `.env`. Si más adelante añades un nuevo modelo, creas una nueva migración con `alembic revision --autogenerate -m "descripción"` y al volver a arrancar la app se aplicará.

### Autenticación y Sesiones (JWT)

El sistema implementa autenticación basada en **tokens JWT** con funcionalidad completa de login/logout y **manejo automático de expiración**.

#### Configuración

Agrega las siguientes variables al archivo `.env`:

```bash
JWT_SECRET_KEY=dev-secret-key-CHANGE-IN-PRODUCTION
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
USE_REFRESH_TOKENS=true
```

**⚠️ IMPORTANTE**: En producción, genera una clave secreta aleatoria segura:
```bash
openssl rand -hex 32
```

#### Endpoints de Autenticación

**Login** - `POST /api/v1/auth/login`
```json
{
  "email": "usuario@example.com",
  "password": "contraseña123"
}
```
Respuesta exitosa (con refresh tokens habilitados):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Refresh** - `POST /api/v1/auth/refresh`
- Renueva el access token sin re-autenticarse
- Requiere un refresh token válido
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Logout** - `POST /api/v1/auth/logout`
- Requiere token JWT en header: `Authorization: Bearer <token>`
- Invalida el token agregándolo a una blacklist
- El token no podrá ser reutilizado después del logout

**Validar Token** - `POST /api/v1/auth/validate`
- Verifica si un token es válido y no ha expirado
- Útil para decidir si refrescar el token
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Información del Usuario** - `GET /api/v1/auth/me`
- Requiere autenticación
- Devuelve información del usuario extraída del token

#### Manejo de Expiración Automática

El backend devuelve respuestas estructuradas cuando un token expira:

```json
{
  "detail": {
    "message": "Token ha expirado. Por favor, inicie sesión nuevamente.",
    "error_code": "TOKEN_EXPIRED",
    "redirect_to_login": true
  }
}
```

**Códigos de error:**
- `TOKEN_EXPIRED` - El access token ha expirado (refrescar con refresh token)
- `TOKEN_INVALID` - Token malformado o inválido
- `TOKEN_REVOKED` - Token invalidado por logout
- `REFRESH_TOKEN_EXPIRED` - Refresh token expirado (re-autenticarse)

**Para Desarrolladores de Frontend:**
Consulta [docs/FRONTEND_TOKEN_HANDLING.md](docs/FRONTEND_TOKEN_HANDLING.md) para:
- Implementar refresh automático de tokens
- Manejar errores de expiración
- Ejemplos completos en JavaScript/React
- Mejores prácticas de seguridad

#### Proteger Endpoints

Para proteger cualquier endpoint, usa la dependencia `get_current_user_id`:

```python
from uuid import UUID
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user_id

router = APIRouter()

@router.get("/protected")
def protected_endpoint(user_id: UUID = Depends(get_current_user_id)):
    return {"message": f"Hola usuario {user_id}"}
```

#### Implementación del Logout y Blacklist

El sistema de logout funciona mediante una **blacklist de tokens**:

1. Al hacer logout, el token se agrega a la blacklist en memoria
2. Todas las peticiones subsecuentes con ese token son rechazadas
3. Los tokens expiran automáticamente según su tiempo de vida

**Nota**: La blacklist actual es en memoria. Para producción con múltiples instancias, se recomienda usar Redis con TTL.

- Documentación interactiva: **http://127.0.0.1:8000/docs**
- Health: **http://127.0.0.1:8000/health**
- Items: **http://127.0.0.1:8000/api/v1/items**
- Auth: **http://127.0.0.1:8000/api/v1/auth/login**

## Ejemplo de uso (Items)


- `GET /api/v1/items/` — listar items
- `GET /api/v1/items/{id}` — obtener un item
- `POST /api/v1/items/` — crear item (body: `{"name": "Mi item", "description": "opcional"}`)
- `DELETE /api/v1/items/{id}` — eliminar item
