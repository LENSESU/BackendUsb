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
cd BACKEND
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

- Documentación interactiva: **http://127.0.0.1:8000/docs**
- Health: **http://127.0.0.1:8000/health**
- Items: **http://127.0.0.1:8000/api/v1/items**

## Ejemplo de uso (Items)


- `GET /api/v1/items/` — listar items
- `GET /api/v1/items/{id}` — obtener un item
- `POST /api/v1/items/` — crear item (body: `{"name": "Mi item", "description": "opcional"}`)
- `DELETE /api/v1/items/{id}` — eliminar item
