"""Dependencias de autenticación para proteger endpoints."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import TokenExpiredError, TokenInvalidError, decode_access_token
from app.core.token_blacklist import is_token_blacklisted

# Esquema de seguridad Bearer (JWT en header Authorization)
security = HTTPBearer()


def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
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

