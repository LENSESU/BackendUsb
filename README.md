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
<<<<<<< HEAD
cd BackendUsb
=======
cd BACKEND
>>>>>>> 405b93180bc284fa7bd67c044e1a84560b08d05f
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

### CI/CD (GitHub Actions)

Este repositorio incluye un workflow de CI en `.github/workflows/ci.yml` que se ejecuta en:

- Push a la rama `dev`.
- Pull requests hacia `dev` y `main`.

El pipeline realiza:

- **Linting con Ruff** sobre la carpeta `app/`.
- **Chequeo básico de sintaxis** con `python -m compileall app`.

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

- Documentación interactiva: **http://127.0.0.1:8000/docs**
- Health: **http://127.0.0.1:8000/health**
- Items: **http://127.0.0.1:8000/api/v1/items**

## Ejemplo de uso (Items)


- `GET /api/v1/items/` — listar items
- `GET /api/v1/items/{id}` — obtener un item
- `POST /api/v1/items/` — crear item (body: `{"name": "Mi item", "description": "opcional"}`)
- `DELETE /api/v1/items/{id}` — eliminar item
