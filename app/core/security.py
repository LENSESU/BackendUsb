"""Utilidades de seguridad: JWT y hashing de contraseñas."""

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Contexto para hashear y verificar contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    """Tipos de tokens JWT."""

    ACCESS = "access"
    REFRESH = "refresh"


class TokenValidationError(Exception):
    """Error base para validación de tokens."""

    pass


class TokenExpiredError(TokenValidationError):
    """Token ha expirado."""

    pass


class TokenInvalidError(TokenValidationError):
    """Token es inválido."""

    pass


def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Crea un token JWT de acceso con los datos proporcionados.
    
    Args:
        data: Diccionario con los claims a incluir en el token (ej: {"sub": user_id})
        expires_delta: Tiempo de expiración personalizado (opcional)
    
    Returns:
        Token JWT codificado como string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": TokenType.ACCESS.value,
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Crea un token JWT de refresco (refresh token) con mayor duración.
    
    Los refresh tokens solo se usan para obtener nuevos access tokens,
    no para acceder a recursos protegidos.
    
    Args:
        data: Diccionario con los claims a incluir (normalmente solo {"sub": user_id})
    
    Returns:
        Refresh token JWT codificado como string
    """
    to_encode = data.copy()
    
    expire = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days
    )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": TokenType.REFRESH.value,
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str, validate_type: bool = True) -> dict[str, Any] | None:
    """
    Decodifica y valida un token JWT.
    
    Args:
        token: Token JWT a decodificar
        validate_type: Si True, valida que sea un access token
    
    Returns:
        Diccionario con los claims del token si es válido, None si no
        
    Raises:
        TokenExpiredError: Si el token ha expirado
        TokenInvalidError: Si el token es inválido o del tipo incorrecto
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        
        # Validar tipo de token si se requiere
        if validate_type and payload.get("type") != TokenType.ACCESS.value:
            raise TokenInvalidError("Token no es de tipo access")
        
        return payload
        
    except ExpiredSignatureError:
        raise TokenExpiredError("Token ha expirado")
    except JWTError as e:
        raise TokenInvalidError(f"Token inválido: {str(e)}")


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida un refresh token.
    
    Args:
        token: Refresh token JWT a decodificar
    
    Returns:
        Diccionario con los claims del token
        
    Raises:
        TokenExpiredError: Si el token ha expirado
        TokenInvalidError: Si el token es inválido o no es un refresh token
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        
        # Validar que sea un refresh token
        if payload.get("type") != TokenType.REFRESH.value:
            raise TokenInvalidError("Token no es de tipo refresh")
        
        return payload
        
    except ExpiredSignatureError:
        raise TokenExpiredError("Refresh token ha expirado")
    except JWTError as e:
        raise TokenInvalidError(f"Refresh token inválido: {str(e)}")


def validate_token(token: str) -> tuple[bool, str | None]:
    """
    Valida un token y devuelve su estado.
    
    Args:
        token: Token JWT a validar
    
    Returns:
        Tupla (es_válido, mensaje_error)
        - (True, None) si el token es válido
        - (False, mensaje) si el token es inválido o expirado
    """
    try:
        decode_access_token(token, validate_type=False)
        return (True, None)
    except TokenExpiredError as e:
        return (False, str(e))
    except TokenInvalidError as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"Error desconocido: {str(e)}")

