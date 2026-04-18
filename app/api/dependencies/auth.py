"""Dependencias de autenticación para proteger endpoints.

Módulo modificado para issues #61 y #63:

- **#61 – Proteger endpoints del backend:**
  Se agregaron las dependencias ``get_current_role_id``, ``get_current_role_name``
  y la factory ``require_role()`` que permite decorar cualquier endpoint con
  ``dependencies=[Depends(require_role("Administrador", "Estudiante"))]`` para
  restringir acceso por rol.  ``require_role`` lee el claim ``role_name``
  directamente del JWT (embebido en el login), por lo que **no hace consultas
  adicionales a la BD** en cada petición.

- **#63 – Validar accesos cruzados:**
  ``get_current_user_id`` (ya existente) se reutiliza en las rutas de Items
  para comparar el ``owner_id`` del recurso con el usuario autenticado.
  ``get_current_role_name`` se usa para permitir que un Administrator
  haga bypass de la validación de ownership.

Dependencias existentes antes de #61/#63 (no modificadas):
  - ``get_current_token``  → valida JWT + blacklist.
  - ``get_current_user_id`` → extrae ``sub`` (UUID) del JWT.

Dependencias NUEVAS añadidas para #61/#63:
  - ``get_current_role_id``   → extrae ``role_id`` (UUID) del JWT.
  - ``get_current_role_name`` → extrae ``role_name`` (str) del JWT.
  - ``require_role(*roles)``  → factory que retorna una dependencia que
    valida que el ``role_name`` del token esté en la lista de roles permitidos.
"""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import TokenExpiredError, TokenInvalidError, decode_access_token
from app.core.token_blacklist import is_token_blacklisted

# Esquema de seguridad Bearer (JWT en header Authorization)
# auto_error=False permite manejar credenciales ausentes y retornar 401 en lugar de 403
security = HTTPBearer(auto_error=False)


def get_current_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """
    Extrae y valida el token JWT del header Authorization.

    Verifica que:
    - El token esté presente
    - El token no esté en la blacklist
    - El token sea válido y no haya expirado

    Returns:
        Token JWT válido

    Raises:
        HTTPException 401: Si el token es inválido, expirado o blacklisted
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "No autenticado. Proporcione un token de acceso.",
                "error_code": "MISSING_TOKEN",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verificar si el token está blacklisted (logout)
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token ha sido revocado. Inicie sesión nuevamente.",
                "error_code": "TOKEN_REVOKED",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decodificar y validar el token
    try:
        decode_access_token(token, validate_type=True)
        return token
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token ha expirado. Inicie sesión nuevamente.",
                "error_code": "TOKEN_EXPIRED",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": str(e),
                "error_code": "TOKEN_INVALID",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(token: str = Depends(get_current_token)) -> UUID:
    """
    Extrae el ID del usuario del token JWT.

    Args:
        token: Token JWT válido

    Returns:
        UUID del usuario autenticado

    Raises:
        HTTPException: Si el token no contiene un user_id válido
    """
    try:
        payload = decode_access_token(token, validate_type=True)
    except (TokenExpiredError, TokenInvalidError):
        # Estos errores ya se manejan en get_current_token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "No se pudo validar las credenciales",
                "error_code": "INVALID_CREDENTIALS",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "No se pudo validar las credenciales",
                "error_code": "INVALID_CREDENTIALS",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token no contiene información de usuario",
                "error_code": "MISSING_USER_INFO",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "ID de usuario inválido en token",
                "error_code": "INVALID_USER_ID",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# NUEVAS dependencias añadidas para #61 (protección de endpoints)
# ---------------------------------------------------------------------------


def get_current_role_id(token: str = Depends(get_current_token)) -> UUID:
    """
    [NUEVO – #61] Extrae el ``role_id`` (UUID) del payload del token JWT.

    Se usa internamente; para validar permisos por nombre de rol
    es preferible usar ``get_current_role_name`` o ``require_role``.

    Returns:
        UUID del rol del usuario autenticado

    Raises:
        HTTPException 401: Si el token no contiene role_id válido
    """
    try:
        payload = decode_access_token(token, validate_type=True)
    except (TokenExpiredError, TokenInvalidError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "No se pudo validar las credenciales",
                "error_code": "INVALID_CREDENTIALS",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_id: str | None = payload.get("role_id") if payload else None

    if role_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token no contiene información de rol",
                "error_code": "MISSING_ROLE_INFO",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return UUID(role_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "ID de rol inválido en token",
                "error_code": "INVALID_ROLE_ID",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_role_name(token: str = Depends(get_current_token)) -> str:
    """
    [NUEVO – #61] Extrae el nombre del rol (``role_name``) del token JWT.

    El claim ``role_name`` se incluye en el JWT durante el login y el
    refresh (ver ``app/api/routes/auth.py``).  De esta forma se evita una
    consulta extra a la tabla ``roles`` en cada petición protegida.

    Posibles valores: ``"Administrator"``, ``"Student"``, ``"Technician"``
    (definidos en el seed ``app/scripts/seed_users.py``).

    Returns:
        Nombre del rol (ej. "Administrator", "Student", "Technician")

    Raises:
        HTTPException 401: Si el token no contiene role_name
    """
    try:
        payload = decode_access_token(token, validate_type=True)
    except (TokenExpiredError, TokenInvalidError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "No se pudo validar las credenciales",
                "error_code": "INVALID_CREDENTIALS",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_name: str | None = payload.get("role_name") if payload else None

    if role_name is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token no contiene nombre de rol. Inicie sesión nuevamente.",
                "error_code": "MISSING_ROLE_NAME",
                "redirect_to_login": True,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return role_name


def require_role(*allowed_role_names: str) -> Callable:
    """
    [NUEVO – #61] Factory de dependencias RBAC para restringir endpoints por rol.

    Cómo funciona:
      1. Recibe una lista de nombres de rol permitidos.
      2. Retorna una función-dependencia que FastAPI ejecuta antes del handler.
      3. La dependencia extrae ``role_name`` del JWT (vía ``get_current_role_name``).
      4. Si el rol NO está en la lista → **HTTP 403 INSUFFICIENT_PERMISSIONS**.
      5. No realiza consultas a la BD (todo se resuelve con el token).

    Ejemplo de uso en un router::

        @router.get(
            "/admin-only",
            dependencies=[Depends(require_role("Administrator"))],
        )
        def admin_endpoint(): ...

        @router.post(
            "/",
            dependencies=[Depends(require_role("Administrator", "Technician"))],
        )
        def restricted_endpoint(): ...

    Args:
        allowed_role_names: Nombres de roles permitidos
            (ej: "Administrador", "Estudiante", "Tecnico")

    Returns:
        Dependencia FastAPI (Callable) que valida el rol del token
    """

    def _check_role(role_name: str = Depends(get_current_role_name)) -> str:
        if role_name not in allowed_role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "No tiene permisos para acceder a este recurso",
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "required_roles": list(allowed_role_names),
                },
            )
        return role_name

    return _check_role


# ---------------------------------------------------------------------------
# Dependencia de servicio de autenticación
# ---------------------------------------------------------------------------
from app.application.services.auth_service import AuthService
from app.infrastructure.adapters.sql_user_repository import SqlUserRepository

def get_auth_service() -> AuthService:
    """
    Construye AuthService con el repositorio SQL de usuarios.
    
    Equivalente a get_incident_service() — sin estado compartido
    porque AuthService no lo necesita.
    """
    return AuthService(user_repository=SqlUserRepository())
