# Changelog - Manejo de Expiración Automática de Tokens

## Resumen de Cambios

Implementación completa del sistema de **manejo automático de expiración de tokens** con refresh tokens y validación.

### Fecha: 4 de Marzo, 2026
### Branch: `feature/auth-session`

---

## 🆕 Nuevas Funcionalidades

### 1. Sistema de Refresh Tokens

- **Access Token**: Corta duración (60 minutos por defecto) para acceder a recursos
- **Refresh Token**: Larga duración (7 días por defecto) para renovar access tokens
- **Rotación de Tokens**: Los refresh tokens usados se invalidan automáticamente

### 2. Endpoints Nuevos

#### `POST /api/v1/auth/refresh`
Renueva un access token usando un refresh token válido.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "nuevo_token...",
  "refresh_token": "nuevo_refresh...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### `POST /api/v1/auth/validate`
Valida si un token es válido actualmente.

**Request:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "valid": true,
  "expired": false,
  "error": null,
  "message": "Token es válido"
}
```

### 3. Respuestas de Error Estructuradas

Todos los errores de autenticación ahora incluyen información estructurada:

```json
{
  "detail": {
    "message": "Token ha expirado. Por favor, inicie sesión nuevamente.",
    "error_code": "TOKEN_EXPIRED",
    "redirect_to_login": true
  }
}
```

**Códigos de Error:**
- `TOKEN_EXPIRED` - Access token expirado (refresar)
- `TOKEN_INVALID` - Token inválido o malformado
- `TOKEN_REVOKED` - Token invalidado por logout
- `REFRESH_TOKEN_EXPIRED` - Refresh token expirado (re-autenticarse)
- `REFRESH_TOKEN_INVALID` - Refresh token inválido
- `INVALID_CREDENTIALS` - Credenciales inválidas
- `MISSING_USER_INFO` - Token no contiene información de usuario
- `INVALID_USER_ID` - ID de usuario inválido en token

### 4. Login Actualizado

El endpoint de login ahora devuelve refresh token:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 📁 Archivos Modificados

### Backend Core

1. **`app/core/config.py`**
   - ✅ Agregada configuración de refresh tokens
   - ✅ `refresh_token_expire_days`: Duración del refresh token
   - ✅ `use_refresh_tokens`: Flag para habilitar/deshabilitar refresh tokens

2. **`app/core/security.py`**
   - ✅ Nuevas excepciones: `TokenExpiredError`, `TokenInvalidError`
   - ✅ Enum `TokenType` para diferenciar access y refresh tokens
   - ✅ `create_refresh_token()`: Crear refresh tokens
   - ✅ `decode_refresh_token()`: Decodificar y validar refresh tokens
   - ✅ `validate_token()`: Validar estado de un token
   - ✅ Mejor manejo de errores con excepciones específicas

### API Layer

3. **`app/api/schemas/auth.py`**
   - ✅ `TokenResponse` actualizado con `refresh_token` y `expires_in`
   - ✅ `RefreshTokenRequest`: Schema para refresh
   - ✅ `TokenValidationRequest`: Schema para validación
   - ✅ `TokenValidationResponse`: Respuesta de validación

4. **`app/api/dependencies/auth.py`**
   - ✅ Manejo mejorado de errores con respuestas estructuradas
   - ✅ Uso de excepciones específicas (`TokenExpiredError`, etc.)
   - ✅ Respuestas con flag `redirect_to_login`

5. **`app/api/routes/auth.py`**
   - ✅ Login actualizado para devolver refresh token
   - ✅ Nuevo endpoint `/refresh` para renovar tokens
   - ✅ Nuevo endpoint `/validate` para validar tokens
   - ✅ Endpoint `/me` mejorado con mejor manejo de errores
   - ✅ Lógica de rotación de refresh tokens

### Configuración

6. **`.env.example`**
   - ✅ Variables de refresh tokens documentadas
   - ✅ `REFRESH_TOKEN_EXPIRE_DAYS=7`
   - ✅ `USE_REFRESH_TOKENS=true`

7. **`requirements.txt`**
   - ℹ️ Sin cambios (dependencias ya existentes)

---

## 📚 Documentación actual

### 1. **`README.md`**
- ✅ Guía principal de instalación y ejecución
- ✅ Sección de autenticación con refresh tokens
- ✅ Credenciales de desarrollo y comandos operativos

### 2. **`docs/README.md`**
- ✅ Índice de documentación suplementaria
- ✅ Convención para evitar duplicar setup y operación

### 3. **`docs/CHANGELOG_TOKEN_EXPIRATION.md`**
- ✅ Historial técnico de la implementación de sesiones
- ✅ Resumen de cambios en tokens, errores y endpoints

---

## 🧪 Tests Actualizados

### `tests/api/test_auth.py`
- ✅ Test de flujo de refresh token
- ✅ Test de endpoint de validación
- ✅ Test de refresh con token inválido
- ✅ Test de estructura de respuestas de error
- ✅ Verificación de flags `redirect_to_login`

---

## 🔧 Configuración Requerida

### Variables de Entorno

Agregar al archivo `.env`:

```bash
# Refresh Tokens
REFRESH_TOKEN_EXPIRE_DAYS=7
USE_REFRESH_TOKENS=true
```

### Sin Cambios en Dependencias

No se requiere instalar nuevas dependencias. Las librerías JWT (`python-jose`) y de hashing (`passlib`) ya estaban instaladas.

---

## 🚀 Guía de Migración

### Para Proyectos Existentes

1. **Actualizar Frontend:**
   - Implementar manejo de refresh tokens siguiendo la sección de autenticación de `README.md`
   - Actualizar manejo de errores para usar `error_code` y `redirect_to_login`
   - Implementar interceptor de peticiones para auto-refresh

2. **Actualizar Almacenamiento:**
   - Guardar `refresh_token` además del `access_token`
   - Guardar `expires_in` para determinar cuándo refrescar proactivamente

3. **Actualizar Lógica de Logout:**
   - Limpiar tanto access como refresh tokens
   - Verificar flag `redirect_to_login` en respuestas 401

### Retrocompatibilidad

✅ **100% Retrocompatible**
- El sistema funciona sin refresh tokens si `USE_REFRESH_TOKENS=false`
- El login sigue devolviendo `access_token` en el mismo formato
- Clientes antiguos pueden seguir funcionando sin cambios

---

## 📊 Diagrama de Flujo

### Flujo con Auto-Refresh

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       │ 1. Petición con Access Token
       ▼
┌─────────────┐
│   Backend   │
└──────┬──────┘
       │
       ├─► Token válido → 200 OK
       │
       └─► Token expirado (401)
              │
              │ error_code: TOKEN_EXPIRED
              ▼
       ┌─────────────┐
       │   Cliente   │ 2. Detecta expiración
       └──────┬──────┘
              │
              │ 3. POST /auth/refresh
              │    { refresh_token: "..." }
              ▼
       ┌─────────────┐
       │   Backend   │
       └──────┬──────┘
              │
              ├─► Refresh válido
              │   → 200 OK
              │   { access_token, refresh_token }
              │
              └─► Refresh expirado
                  → 401 UNAUTHORIZED
                  → redirect_to_login: true
                  → Cliente redirige a /login
```

---

## ✅ Checklist de Implementación

- [x] Configuración de refresh tokens
- [x] Creación y validación de refresh tokens
- [x] Endpoint `/auth/refresh`
- [x] Endpoint `/auth/validate`
- [x] Sistema de blacklist para refresh tokens
- [x] Respuestas de error estructuradas
- [x] Códigos de error estándar
- [x] Documentación de frontend
- [x] Ejemplos de integración
- [x] Tests unitarios
- [x] Actualización de README
- [x] Variables de entorno documentadas
- [x] Retrocompatibilidad verificada

---

## 🎯 Próximos Pasos Sugeridos

### Mejoras Futuras (Opcional)

1. **Redis para Blacklist**
   - Migrar blacklist de memoria a Redis
   - Permite múltiples instancias del backend
   - TTL automático para tokens expirados

2. **HttpOnly Cookies**
   - Implementar opción de usar cookies para refresh tokens
   - Mayor seguridad contra XSS

3. **Métricas de Tokens**
   - Endpoint para ver tokens activos por usuario
   - Revocar todos los tokens de un usuario
   - Historial de sesiones

4. **Rate Limiting**
   - Limitar intentos de refresh
   - Prevenir abuso del endpoint de refresh

5. **Notificaciones de Sesión**
   - Email cuando se inicia sesión desde nuevo dispositivo
   - Notificar sobre actividad inusual

---

## 📖 Recursos Adicionales

- **Guía principal**: `README.md`
- **Índice de docs**: `docs/README.md`
- **Historial técnico**: `docs/CHANGELOG_TOKEN_EXPIRATION.md`
- **Tests**: `tests/api/test_auth.py`
- **Swagger UI**: http://127.0.0.1:8000/docs

---

## 👥 Contribuciones

Sistema implementado por: GitHub Copilot
Fecha: 4 de Marzo, 2026
Branch: `feature/auth-session`

---

## 📝 Notas

- El sistema es completamente funcional y listo para producción
- Recomendado usar Redis para blacklist en producción
- El frontend debe implementar el manejo de refresh tokens según el flujo documentado en `README.md`
- Todos los tests pasan sin errores
- Código cumple con PEP 8 y ruff linting
