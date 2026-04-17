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

## Documentación

- Este archivo es la fuente principal para instalación, configuración, migraciones y operación del backend.
- La documentación complementaria y notas históricas están indexadas en [docs/README.md](docs/README.md).

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
ALLOWED_EMAIL_DOMAINS=["correo.usbcali.edu.co"]
```

> Consulta `.env.example` para ver todas las variables disponibles con sus descripciones.

### Google Cloud Storage para evidencias

La carga de evidencias de incidentes puede persistirse en **Google Cloud Storage**.

#### Flujo recomendado para desarrolladores (ADC sin JSON)

**Precondición:** el administrador ya agregó tu correo en IAM con permisos sobre el bucket.

##### Autenticación desde cero (solo Docker CLI)

Backend levantado con `docker compose up -d`. Sustituye `PROJECT_ID` por el ID de tu proyecto en GCP.

**Paso 0 (opcional).** Listar proyectos para obtener el Project ID:

```bash
docker compose exec backend gcloud projects list
```

**Pasos 1–5.**

```bash
docker compose exec -it backend gcloud auth login
docker compose exec backend gcloud config set project PROJECT_ID
docker compose exec -it backend gcloud auth application-default login
docker compose exec backend gcloud auth application-default set-quota-project PROJECT_ID
docker compose exec backend gcloud auth application-default print-access-token
```

##### Si bajas el contenedor (`docker compose down`)

Las credenciales ADC se guardan **dentro** del contenedor. Al hacer `docker compose down` (o reconstruir la imagen) se pierden. Para volver a usarlas:

1. Levanta de nuevo el backend: `docker compose up -d backend`
2. Repite al menos el **login ADC** y el **quota project** (sustituye `PROJECT_ID`):
   ```bash
   docker compose exec -it backend gcloud auth application-default login
   docker compose exec backend gcloud auth application-default set-quota-project PROJECT_ID
   ```

En producción se suele usar una **cuenta de servicio** y montar su JSON (o variable de entorno) en lugar de ADC de usuario.

##### Configura en `.env`

Usa el mismo `PROJECT_ID` y nombre de bucket que tengas en GCP:

```bash
GCS_ENABLED=true
GCS_PROJECT_ID=tu-proyecto-gcp
GCS_BUCKET_NAME=usb-incidentes-evidencias
GCS_EVIDENCE_PREFIX=incidents/evidence
GCS_MAKE_PUBLIC=false
```

**Notas:**

- El backend usa **Application Default Credentials (ADC)**; no requiere ni lee rutas JSON.
- Cada desarrollador usa su propia identidad; no se comparten llaves ni archivos sensibles.
- En Cloud Run/GKE/GCE, ADC se resuelve con la identidad del workload (sin cambios de código).
- Si `GCS_MAKE_PUBLIC=true`, cada archivo se marca público y se retorna `file_url`.
- Si `GCS_ENABLED=false`, el sistema usa un adaptador in-memory (útil para tests y desarrollo sin GCP).

#### Probar el endpoint de carga de evidencias Swagger

Crear un incidente de prueba con claves foráneas válidas:

```bash
python -m app.scripts.create_incident_via_api
```

Anota el `ID del incidente` que se imprime en consola.

   - Pulsa en el endpoint, luego en **Try it out**.
   - Copia el `ID del incidente` generado en el paso 1 en el parámetro `incident_id`.
   - En el campo `photo`, selecciona un archivo de imagen JPG o PNG desde tu equipo.
   - Ejecuta la petición con **Execute**.

Verificar en la respuesta que:
   - `storage_object_name` contiene la ruta en el bucket.
   - `file_url` tenga la URL de acceso (si `GCS_MAKE_PUBLIC=true`).
   - `incident_id` coincida con el UUID usado en la llamada.

### Ejecutar en local (uvicorn)

Asegúrate de haber configurado `.env`.

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en `http://127.0.0.1:8080`.

### Ejecutar con Docker

No necesitas cambiar nada en el `.env` para usar Docker. El `docker-compose.yml` sobreescribe `POSTGRES_HOST` automáticamente con el nombre interno del servicio (`postgres`). Solo asegúrate de tener Docker corriendo.

Al levantar Docker, el backend queda configurado para:

- ejecutar migraciones automáticamente al arrancar
- ejecutar el seed de usuarios automáticamente al arrancar
- dejar disponibles las credenciales de desarrollo si no existen todavía

Construir y levantar todos los servicios (backend + PostgreSQL + Mailpit):

```bash
docker compose up --build
```

Para ejecutar en segundo plano:

```bash
docker compose up -d --build
```

Con Docker, la API queda en `http://127.0.0.1:8080`, PostgreSQL en `localhost:5432` y Mailpit (cliente de correo local) en `http://localhost:8025`.

> **Nota**: `--build` solo es necesario la primera vez o cuando cambies el `Dockerfile` o `requirements.txt`. Para el resto de casos basta con `docker compose up`.

### Migraciones (Alembic)

**No tienes que hacer nada a mano.** Al arrancar la app (con Postgres corriendo), se aplican solas las migraciones: se crean o actualizan las tablas en la base de datos. Solo asegúrate de tener Postgres levantado y las variables de entorno (`POSTGRES_*` o `DATABASE_URL`) en `.env`. Si más adelante añades un nuevo modelo, creas una nueva migración con `alembic revision --autogenerate -m "descripción"` y al volver a arrancar la app se aplicará.

### Poblar Base de Datos con Usuarios de Prueba

Con `docker compose up`, este seed corre automáticamente al arrancar el backend. Si quieres ejecutarlo manualmente otra vez, usa:

```bash
python -m app.scripts.seed_users
```

Esto crea los siguientes usuarios con sus roles:

| Rol | Email | Password |
|---|---|---|
| Administrador | admin@usbcali.edu.co | admin123 |
| Estudiante | estudiante@correo.usbcali.edu.co | estudiante123 |
| Técnico | tecnico@usbcali.edu.co | tecnico123 |

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

- Documentación interactiva (Swagger): **http://127.0.0.1:8080/docs**
- Health check: **http://127.0.0.1:8000/health**
- Auth: **http://127.0.0.1:8080/api/v1/auth/login**
- Mailpit (correos locales): **http://localhost:8025**

---

## Guía de consumo para el equipo Frontend

### Configuración base

| Variable | Valor (local) |
|---|---|
| Base URL | `http://127.0.0.1:8080` |
| Prefijo de rutas | `/api/v1` |
| CORS permitidos | `http://localhost:3000`, `http://127.0.0.1:3000` |
| Content-Type | `application/json` (excepto upload de evidencias) |

Todos los endpoints protegidos requieren el header:
```
Authorization: Bearer <access_token>
```

---

### Flujo de autenticación completo

```
1. POST /api/v1/auth/register   → recibe OTP en correo
2. POST /api/v1/auth/verify-otp → activa cuenta, devuelve tokens
3. POST /api/v1/auth/login      → inicio de sesión normal
4. POST /api/v1/auth/refresh    → renueva access_token sin re-login
5. POST /api/v1/auth/logout     → invalida el token actual
```

#### 1. Registro — `POST /api/v1/auth/register`

```json
{
  "first_name": "María",
  "last_name": "López",
  "email": "mlopez@correo.usbcali.edu.co",
  "password": "Segura123!",
  "role_id": null
}
```

**Reglas de validación:**

| Campo | Regla |
|---|---|
| `first_name` / `last_name` | 2-255 caracteres. Solo letras, espacios, apóstrofes y guiones. Acepta tildes y ñ. |
| `email` | Debe terminar en un dominio permitido (por defecto `@correo.usbcali.edu.co`). |
| `password` | Mínimo 8 caracteres, al menos 1 mayúscula, 1 minúscula, 1 número y 1 caracter especial (`@$!%*?&._-`). |
| `role_id` | Opcional. Si no se envía (o se envía `null`) se asigna el rol **Estudiante** por defecto. |

**Respuesta exitosa (201):**
```json
{ "message": "Código de verificación enviado a tu correo" }
```

**Errores comunes:**
- `400` — validación de campos
- `409` — el correo ya está registrado
- `502` — fallo al enviar el correo (problema en el servidor de correo)

#### 2. Verificar OTP — `POST /api/v1/auth/verify-otp`

```json
{
  "email": "mlopez@correo.usbcali.edu.co",
  "code": "123456"
}
```

**Respuesta exitosa (200):** igual que el login (ver sección siguiente).

Si el código expiró, usa `POST /api/v1/auth/resend-otp`:
```json
{ "email": "mlopez@correo.usbcali.edu.co" }
```
Si el reenvío está en periodo de espera, recibirás un `429` con los segundos restantes en el mensaje.

#### 3. Login — `POST /api/v1/auth/login`

```json
{
  "email": "mlopez@correo.usbcali.edu.co",
  "password": "Segura123!"
}
```

**Respuesta exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Guarda ambos tokens. `expires_in` está en segundos.

El JWT contiene estas claims (no necesitas pedirlas al backend):
- `sub` → UUID del usuario
- `email` → correo del usuario
- `role_id` → UUID del rol
- `role_name` → `"Administrator"` | `"Student"` | `"Technician"`

#### 4. Refrescar token — `POST /api/v1/auth/refresh`

Llama a este endpoint **antes de que expire** el `access_token` (o cuando recibas `TOKEN_EXPIRED`):

```json
{ "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

**Respuesta (200):** igual que el login. El refresh token anterior queda invalidado y se emite uno nuevo (rotación).

#### 5. Logout — `POST /api/v1/auth/logout`

Solo necesita el header `Authorization`. Sin body.

**Respuesta (200):**
```json
{ "message": "Sesión cerrada exitosamente" }
```

#### Información del usuario autenticado — `GET /api/v1/auth/me`

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "mlopez@correo.usbcali.edu.co",
  "role_id": "7f3e4c2a-1b5d-4e8f-9a2c-3d6e7f8b9c0d"
}
```

#### Validar token — `POST /api/v1/auth/validate`

```json
{ "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

```json
{
  "valid": true,
  "error": null,
  "expired": false,
  "message": null
}
```

---

### Manejo de errores de autenticación

Cuando un token falla, el backend devuelve `401` con esta estructura:

```json
{
  "detail": {
    "message": "Token ha expirado. Por favor, inicie sesión nuevamente.",
    "error_code": "TOKEN_EXPIRED",
    "redirect_to_login": true
  }
}
```

| `error_code` | Acción recomendada |
|---|---|
| `TOKEN_EXPIRED` | Llama a `/auth/refresh` con el refresh token |
| `TOKEN_INVALID` | Redirigir al login |
| `TOKEN_REVOKED` | Redirigir al login (hizo logout en otra pestaña) |
| `REFRESH_TOKEN_EXPIRED` | Redirigir al login, el usuario debe autenticarse de nuevo |
| `INSUFFICIENT_PERMISSIONS` (`403`) | Mostrar mensaje de acceso denegado |

---

### Roles y permisos

| Rol | `role_name` en JWT | Puede hacer |
|---|---|---|
| Administrador | `"Administrator"` | Todo, incluyendo gestión de categorías y datos de otros usuarios |
| Estudiante | `"Student"` | Crear incidentes/sugerencias propios, no puede asignar técnico |
| Técnico | `"Technician"` | Leer y editar incidentes, no puede gestionar categorías |

---

### Patrón de paginación

Todos los listados usan los mismos query params y respuesta:

**Query params:** `?page=1&limit=10` (limit máximo: 100)

**Respuesta:**
```json
{
  "page": 1,
  "limit": 10,
  "total": 47,
  "total_pages": 5,
  "items": [...]
}
```

---

### Incidentes — `/api/v1/incidents`

Todos los endpoints requieren autenticación (cualquier rol).

#### Crear incidente — `POST /api/v1/incidents/`

```json
{
  "categoria_id": "uuid-de-la-categoria",
  "descripcion": "El proyector del aula 304 no enciende.",
  "lugar_campus": "Central",
  "latitud": 3.3958,
  "longitud": -76.5317,
  "estado": "open",
  "prioridad": "high",
  "foto_antes_id": null
}
```

El `student_id` se asigna automáticamente desde el JWT — no lo envíes.

**Valores válidos para `lugar_campus`:**
`Biblioteca`, `Lago`, `Cedro`, `Central`, `Farrallones`, `Parqueadero_estudiantes`, `Parque tecnologico`, `Naranjos`, `Higuerones`, `Cancha`, `Otros`

**Respuesta (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "student_id": "uuid-del-estudiante",
  "technician_id": null,
  "category_id": "uuid-de-la-categoria",
  "description": "El proyector del aula 304 no enciende.",
  "campus_place": "Central",
  "latitude": 3.3958,
  "longitude": -76.5317,
  "status": "open",
  "priority": "high",
  "before_photo_id": null,
  "after_photo_id": null,
  "created_at": "2026-04-16T10:30:00Z",
  "updated_at": null
}
```

#### Actualizar incidente — `PATCH /api/v1/incidents/{incident_id}`

Envía solo los campos que quieres modificar:

```json
{
  "estado": "in_progress",
  "tecnico_id": "uuid-del-tecnico"
}
```

**Restricciones por rol:**
- **Student**: solo puede editar sus propios incidentes. No puede enviar `tecnico_id`.
- **Technician / Administrator**: puede editar cualquier incidente y asignar técnico.

#### Subir evidencia fotográfica — `POST /api/v1/incidents/{incident_id}/evidence`

Usa `multipart/form-data` (no JSON):

```
Content-Type: multipart/form-data

photo: <archivo JPG o PNG>
```

**Respuesta (201):**
```json
{
  "incident_id": "550e8400-...",
  "filename": "foto.jpg",
  "content_type": "image/jpeg",
  "storage_object_name": "incidents/evidence/550e8400.../foto.jpg",
  "file_url": null,
  "message": "Evidencia fotográfica cargada correctamente"
}
```

`file_url` solo tiene valor si el bucket es público (`GCS_MAKE_PUBLIC=true` en el servidor).

---

### Categorías de incidentes — `/api/v1/categories`

| Endpoint | Roles permitidos |
|---|---|
| `GET /api/v1/categories/` | Todos |
| `GET /api/v1/categories/{id}` | Todos |
| `POST /api/v1/categories/` | Solo Administrator |
| `PATCH /api/v1/categories/{id}` | Solo Administrator |
| `DELETE /api/v1/categories/{id}` | Solo Administrator |

**Crear categoría (solo Admin) — `POST /api/v1/categories/`:**
```json
{
  "name": "Infraestructura",
  "description": "Problemas de planta física y edificios"
}
```
`description` es opcional. `name` máximo 100 caracteres, `description` máximo 200.

**Respuesta:**
```json
{
  "id": "uuid",
  "name": "Infraestructura",
  "description": "Problemas de planta física y edificios"
}
```

---

### Sugerencias — `/api/v1/suggestions`

Todos los endpoints requieren autenticación (cualquier rol).

#### Crear sugerencia — `POST /api/v1/suggestions/`

```json
{
  "estudiante_id": "uuid-del-estudiante",
  "titulo": "Más tomacorrientes en la biblioteca",
  "contenido": "En el segundo piso solo hay 2 tomas para más de 50 estudiantes.",
  "total_votos": 0,
  "foto_id": null
}
```

`total_votos` es opcional (defecto `0`). `titulo` máximo 200 caracteres.

**Listar las más votadas — `GET /api/v1/suggestions/popular`:**

Usa los mismos query params de paginación. Devuelve un formato compacto:
```json
{
  "items": [
    { "id": "uuid", "titulo": "Más tomacorrientes en la biblioteca", "total_votos": 34 }
  ]
}
```

#### Actualizar sugerencia — `PATCH /api/v1/suggestions/{suggestion_id}`

```json
{
  "total_votos": 35,
  "comentario_institucional": "En revisión por el área de infraestructura."
}
```

`comentario_institucional` es el campo para que el administrador responda oficialmente.

---

### Dashboard — `GET /api/v1/dashboard/`

No requiere parámetros. Devuelve un resumen personalizado:

```json
{
  "user": {
    "user_id": "uuid",
    "email": "mlopez@correo.usbcali.edu.co",
    "role_id": "uuid"
  },
  "recentIncidents": [
    {
      "id": "uuid",
      "category_id": "uuid",
      "categoria": "Infraestructura",
      "description": "El proyector del aula 304 no enciende.",
      "status": "open",
      "priority": "high",
      "created_at": "2026-04-16T10:30:00Z"
    }
  ],
  "suggestions": [
    { "id": "uuid", "titulo": "Más tomacorrientes", "total_votos": 34 }
  ]
}
```

Devuelve los 5 incidentes más recientes y las 5 sugerencias más votadas.
