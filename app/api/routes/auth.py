"""Rutas de autenticación: login, logout, refresh, validación.

Modificaciones para #61 (Proteger endpoints del backend):
  - ``login()``:  el payload del JWT ahora incluye el claim ``role_name``
    (ej. "Administrator", "Student", "Technician") resuelto desde la tabla
    ``roles``.  Esto permite que ``require_role()`` valide permisos sin
    consultas extra a la BD en cada petición.
  - ``refresh_access_token()``: mismo cambio — el nuevo access token
    también lleva ``role_name`` para mantener consistencia.
  - Se añadió la importación de ``RoleModel``.

Ningún endpoint de este módulo fue eliminado ni renombrado.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_token
from app.api.dependencies.otp import get_otp_service
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
from app.api.schemas.otp import (
    OtpSentResponse,
    RegisterRequest,
    ResendOtpRequest,
    VerifyOtpRequest,
)
from app.application.services.otp_service import OtpService
from app.application.services.verification_code_service import generate_and_store
from app.core.config import settings
from app.core.email import send_verification_code
from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    validate_token,
    verify_password,
)
from app.core.token_blacklist import add_token_to_blacklist, is_token_blacklisted
from app.infrastructure.database.models import RoleModel, UserModel

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
    # Validar campos obligatorios y formato
    email = (credentials.email or "").strip()
    password = (credentials.password or "").strip()

    if not email and not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo y la contraseña son obligatorios",
        )
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo es obligatorio",
        )
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña es obligatoria",
        )

    import re

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formato del correo electrónico no es válido",
        )

    db = get_db_session()
    stmt = select(UserModel).where(UserModel.email == email)
    user = db.scalar(stmt)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, user.password_hash):
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

    # [NUEVO – #61] Resolver nombre del rol para incluirlo en el JWT.
    # Esto permite que require_role() valide RBAC sin queries extra por request.
    stmt_role = select(RoleModel).where(RoleModel.id == user.role_id)
    role = db.scalar(stmt_role)
    if role:
        token_data["role_name"] = role.name

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

    # [NUEVO – #61] Incluir role_name en el token renovado (igual que en login).
    stmt_role = select(RoleModel).where(RoleModel.id == user.role_id)
    role_obj = db.scalar(stmt_role)
    if role_obj:
        token_data["role_name"] = role_obj.name

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


@router.post(
    "/register",
    response_model=OtpSentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    otp_service: OtpService = Depends(get_otp_service),
) -> OtpSentResponse:
    db = get_db_session()

    stmt = select(UserModel).where(UserModel.email == data.email)
    existing_user = db.scalar(stmt)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    user = UserModel(
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=data.role_id,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        await otp_service.generate_and_send(user_id=user.id, email=user.email)
    except Exception:
        db.delete(user)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo enviar el correo de verificación. Intenta de nuevo.",
        )

    return OtpSentResponse()


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(
    data: VerifyOtpRequest,
    otp_service: OtpService = Depends(get_otp_service),
) -> TokenResponse:
    """
    Verifica el OTP recibido por email y activa la cuenta del usuario.

    Si el OTP es válido, activa el usuario y retorna tokens JWT listos
    para usar, igual que /login. Si el OTP expiró o es incorrecto, retorna 400.

    Args:
        data: Email del usuario y código OTP

    Returns:
        Tokens JWT (access + refresh)

    Raises:
        HTTPException 404: Si el email no existe
        HTTPException 400: Si el OTP es inválido o expiró
    """
    db = get_db_session()

    # Buscar usuario por email
    stmt = select(UserModel).where(UserModel.email == data.email)
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    is_valid = otp_service.verify(user_id=user.id, code=data.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido o expirado",
        )

    # Activar usuario
    user.is_active = True
    db.commit()
    db.refresh(user)

    # Emitir tokens igual que /login
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": str(user.role_id),
    }

    stmt_role = select(RoleModel).where(RoleModel.id == user.role_id)
    role = db.scalar(stmt_role)
    if role:
        token_data["role_name"] = role.name

    access_token = create_access_token(data=token_data)
    refresh_token = None
    if settings.use_refresh_tokens:
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/resend-otp", response_model=OtpSentResponse)
async def resend_otp(
    data: ResendOtpRequest,
    otp_service: OtpService = Depends(get_otp_service),
) -> OtpSentResponse:
    """
    Reenvía el OTP al correo del usuario invalidando el anterior.

    Solo es posible si han pasado al menos otp_resend_cooldown_seconds
    desde el último envío. Si el cooldown no ha pasado, retorna 429
    con los segundos restantes.

    Raises:
        HTTPException 404: Si el email no existe
        HTTPException 400: Si no hay OTP activo para el usuario
        HTTPException 429: Si el cooldown no ha pasado aún
    """
    db = get_db_session()

    stmt = select(UserModel).where(UserModel.email == data.email)
    user = db.scalar(stmt)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    try:
        await otp_service.resend(user_id=user.id, email=user.email)
    except ValueError as e:
        message = str(e)
        if "esperar" in message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return OtpSentResponse()

"""Rutas HTTP para autenticación por email/password."""

from datetime import UTC, datetime, timedelta
import logging
from datetime import datetime, timedelta, timezone
import os

from fastapi import APIRouter, Depends
from jose import jwt

from app.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    LoginResponse,
    RegisterRequest,
    ResendCodeRequest,
    ResendCodeResponse,
)
from app.application.services import AuthService
from app.application.services.verification_code_service import generate_and_store
from app.infrastructure.adapters import PostgresUserRepository

logger = logging.getLogger(__name__)

router = APIRouter()


SECRET_KEY = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def _create_access_token(subject: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_auth_service() -> AuthService:
    """Obtiene el servicio de autenticación."""
    repository = PostgresUserRepository()
    return AuthService(user_repository=repository)


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    user = await auth_service.login_or_register(
        email=payload.email,
        password=payload.password,
    )
    token = _create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Registro explícito de un usuario nuevo."""
    user = await auth_service.register(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )
    token = _create_access_token(user.id)
    return LoginResponse(access_token=token)


@router.post("/resend-code", response_model=ResendCodeResponse)
async def resend_code(payload: ResendCodeRequest) -> ResendCodeResponse:
    """Genera y almacena un nuevo código de verificación para el email.
    En desarrollo el código se registra en logs; en producción se enviaría por email.
    """
    code = generate_and_store(payload.email)
    logger.info("Código de verificación para %s: %s", payload.email, code)
    return ResendCodeResponse()
