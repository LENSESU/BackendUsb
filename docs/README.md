# Documentación del Proyecto

Bienvenido a la documentación del Backend USB.

## Documentos Disponibles

### [AUTHENTICATION.md](AUTHENTICATION.md)
Guía completa de autenticación con JWT:
- Flujo de login/logout
- Ejemplos de uso con curl, Python y JavaScript
- Configuración de seguridad
- Protección de endpoints

### [FRONTEND_TOKEN_HANDLING.md](FRONTEND_TOKEN_HANDLING.md) ⭐ **NUEVO**
Guía para desarrolladores de frontend sobre manejo de tokens:
- **Manejo automático de expiración de tokens**
- **Implementación de refresh tokens**
- Ejemplos completos en JavaScript vanilla y React
- Interceptores de Axios
- Context API de React para autenticación
- Mejores prácticas de seguridad
- Testing

## Documentación Interactiva

La API incluye documentación interactiva generada automáticamente:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Estructura del Proyecto

Ve al [README.md](../README.md) principal para información sobre:
- Instalación y configuración
- Arquitectura hexagonal
- Ejecución con Docker
- Testing y CI/CD

## Nuevos Endpoints de Autenticación

### Manejo de Expiración

El sistema ahora incluye:

- ✅ **Refresh Tokens**: Renueva access tokens sin re-autenticarse
- ✅ **Validación de Tokens**: Verifica si un token es válido
- ✅ **Respuestas estructuradas**: Errores claros con códigos (`TOKEN_EXPIRED`, etc.)
- ✅ **Auto-redireccionamiento**: Flag `redirect_to_login` para que el frontend sepa cuándo redirigir

### Endpoints Disponibles

```
POST /api/v1/auth/login      - Iniciar sesión (devuelve access + refresh token)
POST /api/v1/auth/refresh    - Renovar access token
POST /api/v1/auth/logout     - Cerrar sesión
POST /api/v1/auth/validate   - Validar token
GET  /api/v1/auth/me         - Información del usuario actual
```

## Scripts de Desarrollo

### Poblar Base de Datos con Usuarios de Prueba

```bash
python -m app.scripts.seed_users
```

Crea usuarios de prueba:
- `admin@usb.ve` / `admin123`
- `estudiante@usb.ve` / `estudiante123`
- `tecnico@usb.ve` / `tecnico123`

