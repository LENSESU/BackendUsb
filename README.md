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
- [Docker](https://docs.docker.com/get-docker/) y [Docker Compose](https://docs.docker.com/compose/install/) (para ejecución con contenedores)

## Clonar el repositorio y ejecutar el proyecto

Clona el repositorio:

```bash
git clone https://github.com/Chologalactico/BackendUsb.git
```

Entra al directorio del proyecto:

```bash
cd BackendUsb
```

Crea una nueva rama:

```bash
git checkout -b dev
```

Todo se sube a la rama que creaste, para luego hacer un PR a la rama DEV.

⚠️ **Peligroso**: hacer algún push directo a las ramas `main` o `develop`.

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

### Configuración del entorno (.env)

Copia el archivo de ejemplo y renómbralo:

```bash
cp .env.example .env
```

Abre `.env` y ajusta los valores según tu entorno. Las variables más importantes para empezar son:

```bash
# Host de la base de datos
# El docker-compose.yml sobreescribe esto internamente con el nombre del servicio.
POSTGRES_HOST=localhost

# Migraciones automáticas al arrancar:
RUN_MIGRATIONS_ON_STARTUP=false

# Dominios de correo permitidos para registrarse:
ALLOWED_EMAIL_DOMAINS=["dominio.co", "domain.com"]
```

> Consulta `.env.example` para ver todas las variables disponibles con sus descripciones.

### Google Cloud Storage para evidencias

La carga de evidencias de incidentes puede persistirse en **Google Cloud Storage**.

#### Flujo recomendado para desarrolladores (ADC sin JSON)

Precondicion: el administrador ya agrego tu correo en IAM con permisos sobre el bucket.

1. Abre una terminal de [Google Cloud SDK CLI](https://docs.cloud.google.com/sdk/docs/install-sdk?hl=es-419#latest-version) o cualquier terminal donde `gcloud` este disponible.
2. Inicia sesion con tu correo:

```bash
gcloud auth login
```

3. Selecciona el proyecto activo para trabajar en local:

```bash
gcloud config set project project-1dbf72c5-51f7-430c-932
```

4. Genera/actualiza credenciales ADC para que las use el SDK de Python:

```bash
gcloud auth application-default login
```

5. Asocia el quota project de ADC al mismo proyecto (evita errores de cuota/facturacion):

```bash
gcloud auth application-default set-quota-project project-1dbf72c5-51f7-430c-932
```

6. Verifica rapidamente que ADC quedo activo:

```bash
gcloud auth application-default print-access-token
```

7. Configura en `.env`:

```bash
GCS_ENABLED=true
GCS_PROJECT_ID=tu-proyecto-gcp
GCS_BUCKET_NAME=multimedia_incidents
GCS_EVIDENCE_PREFIX=incidents/evidence
GCS_MAKE_PUBLIC=false
```

Notas:

- El backend usa **Application Default Credentials (ADC)**; no requiere ni lee rutas JSON.
- Cada desarrollador usa su propia identidad; no se comparten llaves ni archivos sensibles.
- En Cloud Run/GKE/GCE, ADC se resuelve con la identidad del workload (sin cambios de código).
- Si `GCS_MAKE_PUBLIC=true`, cada archivo se marca público y se retorna `file_url`.
- Si `GCS_ENABLED=false`, el sistema usa un adaptador in-memory (útil para tests y desarrollo sin GCP).

### Ejecutar en local (uvicorn)

Asegúrate de haber configurado `.env`.

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000`.

### Ejecutar con Docker

No necesitas cambiar nada en el `.env` para usar Docker. El `docker-compose.yml` sobreescribe `POSTGRES_HOST` automáticamente con el nombre interno del servicio (`postgres`). Solo asegúrate de tener Docker corriendo.

Construir y levantar todos los servicios (backend + PostgreSQL + Mailpit):

```bash
docker compose up --build
```

Para ejecutar en segundo plano:

```bash
docker compose up -d --build
```

Con Docker, la API queda en `http://127.0.0.1:8000`, PostgreSQL en `localhost:5432` y Mailpit (cliente de correo local) en `http://localhost:8025`.

> **Nota**: `--build` solo es necesario la primera vez o cuando cambies el `Dockerfile` o `requirements.txt`. Para el resto de casos basta con `docker compose up`.

### Migraciones (Alembic)

**No tienes que hacer nada a mano.** Al arrancar la app (con Postgres corriendo), se aplican solas las migraciones: se crean o actualizan las tablas en la base de datos. Solo asegúrate de tener Postgres levantado y las variables de entorno (`POSTGRES_*` o `DATABASE_URL`) en `.env`. Si más adelante añades un nuevo modelo, creas una nueva migración con `alembic revision --autogenerate -m "descripción"` y al volver a arrancar la app se aplicará.

### Poblar Base de Datos con Usuarios de Prueba

Una vez que la app esté corriendo y las migraciones aplicadas, puedes crear usuarios de prueba con:

```bash
python -m app.scripts.seed_users
```

Esto crea los siguientes usuarios con sus roles:

| Rol | Email | Password |
|---|---|---|
| Administrador | admin@usb.ve | admin123 |
| Estudiante | estudiante@usb.ve | estudiante123 |
| Técnico | tecnico@usb.ve | tecnico123 |

### Probar el endpoint de evidencias de incidentes

**POST /api/v1/incidents/{incident_id}/evidence**: sube una foto de evidencia (JPEG o PNG, máx. 5 MB) y la vincula al incidente en la BD. Necesitas un `incident_id` de un incidente existente.

- **Con Swagger** (ver [URLs útiles](#urls-útiles)): ejecuta `python scripts/test_incident_evidence.py --seed-only`, copia el UUID mostrado y en Swagger → **incidents** → **POST .../evidence** → Try it out → pega el UUID en `incident_id` y selecciona un archivo en `photo` → Execute.

Códigos: **201** éxito; **404** incidente inexistente; **400** formato/tamaño no válido.

---

## Para desarrolladores

### Ejecutar tests

Los tests están en `tests/`. Desde la raíz del proyecto:

```bash
python -m pytest
```

### Linting y formato (Ruff)

```bash
# Revisar errores de linting
python -m ruff check app

# Revisar y aplicar correcciones automáticas
python -m ruff check app --fix

# Comprobar formato
python -m ruff format --check app

# Aplicar formato automáticamente
python -m ruff format app
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
- **Tests** con `pytest`.

Para hacer obligatorio el pipeline antes de fusionar PRs, configura en GitHub:

1. `Settings` → `Branches` → `Branch protection rules`.
2. Protege `dev` y `main`.
3. Añade el check de estado del workflow de CI como requerido.

---

## Autenticación y Sesiones (JWT)

El sistema implementa autenticación basada en **tokens JWT** con funcionalidad completa de login/logout y **manejo automático de expiración**.

### Configuración

Variables relevantes en `.env`:

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

### Endpoints de Autenticación

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
- Renueva el access token sin re-autenticarse.
- Requiere un refresh token válido.
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Logout** - `POST /api/v1/auth/logout`
- Requiere token JWT en header: `Authorization: Bearer <token>`
- Invalida el token agregándolo a una blacklist.
- El token no podrá ser reutilizado después del logout.

**Validar Token** - `POST /api/v1/auth/validate`
- Verifica si un token es válido y no ha expirado.
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Información del Usuario** - `GET /api/v1/auth/me`
- Requiere autenticación.
- Devuelve información del usuario extraída del token.

### Manejo de Expiración Automática

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
- `TOKEN_EXPIRED` — El access token ha expirado (refrescar con refresh token).
- `TOKEN_INVALID` — Token malformado o inválido.
- `TOKEN_REVOKED` — Token invalidado por logout.
- `REFRESH_TOKEN_EXPIRED` — Refresh token expirado (re-autenticarse).

### Proteger Endpoints

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

### Implementación del Logout y Blacklist

El sistema de logout funciona mediante una **blacklist de tokens**:

1. Al hacer logout, el token se agrega a la blacklist en memoria.
2. Todas las peticiones subsecuentes con ese token son rechazadas.
3. Los tokens expiran automáticamente según su tiempo de vida.

> **Nota**: La blacklist actual es en memoria. Para producción con múltiples instancias, se recomienda usar Redis con TTL.

---

## URLs útiles

- Documentación interactiva (Swagger): **http://127.0.0.1:8000/docs**
- Health check: **http://127.0.0.1:8000/health**
- Auth: **http://127.0.0.1:8000/api/v1/auth/login**
- Mailpit (correos locales): **http://localhost:8025**
