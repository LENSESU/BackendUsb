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

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

## Ejecución

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
