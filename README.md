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

- Documentación interactiva: **http://127.0.0.1:8000/docs**
- Health: **http://127.0.0.1:8000/health**
- Items: **http://127.0.0.1:8000/api/v1/items**

## Ejemplo de uso (Items)


- `GET /api/v1/items/` — listar items
- `GET /api/v1/items/{id}` — obtener un item
- `POST /api/v1/items/` — crear item (body: `{"name": "Mi item", "description": "opcional"}`)
- `DELETE /api/v1/items/{id}` — eliminar item
