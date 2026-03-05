"""Rutas de autenticación: login, logout, refresh, validación."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_token
from app.api.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
    ResendCodeRequest,
    ResendCodeResponse,
    TokenResponse,
    TokenValidationRequest,
    TokenValidationResponse,
)
from app.core.config import settings
from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    validate_token,
    verify_password,
)
from app.application.services.verification_code_service import generate_and_store
from app.core.email import send_verification_code
from app.core.token_blacklist import add_token_to_blacklist, is_token_blacklisted
from app.infrastructure.database.models import UserModel

router = APIRouter()


def get_db_session() -> Session:
    """
    Obtiene una sesión de base de datos.

    TODO: Implementar dependency injection con generador para manejo apropiado
    de sesiones (abrir/cerrar automáticamente).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest) -> TokenResponse:
    """
    Autentica un usuario y devuelve tokens JWT (access y opcionalmente refresh).

    Args:
        credentials: Email y contraseña del usuario

    Returns:
        Tokens de acceso y refresco JWT

    Raises:
        HTTPException 401: Si las credenciales son incorrectas
        HTTPException 403: Si el usuario está inactivo
    """
    # TODO: Mover lógica a un servicio de autenticación
    db = get_db_session()

    # Buscar usuario por email
    stmt = select(UserModel).where(UserModel.email == credentials.email)
    user = db.scalar(stmt)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar contraseña
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar que el usuario esté activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    # Datos del usuario para el token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": str(user.role_id),
    }

    # Crear access token
    access_token = create_access_token(data=token_data)

    # Crear refresh token si está habilitado
    refresh_token = None
    if settings.use_refresh_tokens:
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,  # en segundos
    )


@router.post("/resend-code", response_model=ResendCodeResponse)
def resend_verification_code(request: ResendCodeRequest) -> ResendCodeResponse:
    """
    Reenvía un nuevo código de verificación al correo indicado.

    Genera un código de 6 dígitos, lo almacena (válido 10 min) y lo envía por
    email vía SMTP si está configurado (SMTP_ENABLED=true y credenciales).

    Args:
        request: Email al que reenviar el código

    Returns:
        Mensaje de confirmación (no se expone el código por seguridad)
    """
    code = generate_and_store(request.email)
    send_verification_code(request.email, code)
    return ResendCodeResponse()


@router.post("/logout", response_model=LogoutResponse)
def logout(token: str = Depends(get_current_token)) -> LogoutResponse:
    """
    Cierra la sesión del usuario invalidando su token.

    El token se agrega a la blacklist para evitar su reutilización.

    Args:
        token: Token JWT del usuario autenticado

    Returns:
        Mensaje de confirmación de cierre de sesión
    """
    # Agregar token a la blacklist
    add_token_to_blacklist(token)

    return LogoutResponse(message="Sesión cerrada exitosamente")


@router.get("/me")
def get_current_user_info(token: str = Depends(get_current_token)) -> dict:
    """
    Obtiene información del usuario autenticado.

    Endpoint de utilidad para verificar que el token es válido
    y obtener datos del usuario actual.

    Args:
        token: Token JWT del usuario autenticado

    Returns:
        Información del usuario extraída del token
    """
    try:
        payload = decode_access_token(token, validate_type=True)
    except (TokenExpiredError, TokenInvalidError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": str(e),
                "error_code": "TOKEN_ERROR",
                "redirect_to_login": True,
            },
        )

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Token inválido",
                "error_code": "TOKEN_ERROR",
                "redirect_to_login": True,
            },
        )

    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "role_id": payload.get("role_id"),
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest) -> TokenResponse:
    """
    Renueva un access token usando un refresh token válido.

    Permite al cliente obtener un nuevo access token sin re-autenticarse,
    siempre que el refresh token sea válido y no haya expirado.

    Args:
        request: Refresh token del usuario

    Returns:
        Nuevo access token (y opcionalmente nuevo refresh token)

    Raises:
        HTTPException 401: Si el refresh token es inválido o expirado
        HTTPException 404: Si el usuario no existe
    """
    # Verificar que el refresh token no esté en la blacklist
    if is_token_blacklisted(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token ha sido revocado.Inicie sesión nuevamente.",
                "error_code": "REFRESH_TOKEN_REVOKED",
                "redirect_to_login": True,
            },
        )

    # Decodificar el refresh token
    try:
        payload = decode_refresh_token(request.refresh_token)
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token ha expirado. Inicie sesión nuevamente.",
                "error_code": "REFRESH_TOKEN_EXPIRED",
                "redirect_to_login": True,
            },
        )
    except TokenInvalidError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token inválido. Inicie sesión nuevamente.",
                "error_code": "REFRESH_TOKEN_INVALID",
                "redirect_to_login": True,
            },
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no contiene ID de usuario",
        )

    # Verificar que el usuario existe y está activo
    db = get_db_session()
    stmt = select(UserModel).where(UserModel.id == user_id)
    user = db.scalar(stmt)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    # Crear nuevo access token
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": str(user.role_id),
    }

    new_access_token = create_access_token(data=token_data)

    # Opcionalmente crear nuevo refresh token (rotación de tokens)
    new_refresh_token = None
    if settings.use_refresh_tokens:
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
        # Invalidar el refresh token anterior (rotación)
        add_token_to_blacklist(request.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/validate", response_model=TokenValidationResponse)
def validate_access_token(request: TokenValidationRequest) -> TokenValidationResponse:
    """
    Valida si un token es válido y no ha expirado.

    Útil para que el frontend verifique el estado del token antes de hacer
    peticiones o para decidir si debe refrescar el token.

    Args:
        request: Token a validar

    Returns:
        Estado de validación del token
    """
    # Verificar blacklist
    if is_token_blacklisted(request.token):
        return TokenValidationResponse(
            valid=False,
            expired=False,
            error="TOKEN_REVOKED",
            message="Token ha sido revocado",
        )

    # Validar token
    is_valid, error_message = validate_token(request.token)

    if is_valid:
        return TokenValidationResponse(
            valid=True,
            message="Token es válido",
        )

    # Determinar si está expirado o es inválido
    is_expired = "expirado" in error_message.lower() if error_message else False

    return TokenValidationResponse(
        valid=False,
        expired=is_expired,
        error="TOKEN_EXPIRED" if is_expired else "TOKEN_INVALID",
        message=error_message,
    )
