"""Rutas de autenticación: login, logout, refresh, validación, registro y OTP.

Responsabilidades de este módulo
---------------------------------
El router es exclusivamente una capa HTTP: traduce requests a llamadas de
servicio y errores de dominio a respuestas HTTP.  Toda la lógica de negocio
(validación de credenciales, ciclo de vida del usuario, emisión de tokens)
vive en ``AuthService``.

Flujo de cada endpoint
-----------------------
- ``POST /login``       → valida formato, delega en ``AuthService.authenticate``.
- ``POST /logout``      → invalida el token en la blacklist.
- ``GET  /me``          → decodifica el token y retorna claims básicos.
- ``POST /refresh``     → valida blacklist + decodifica refresh token,
                          delega en ``AuthService.refresh_tokens``.
- ``POST /validate``    → comprueba validez del token sin renovarlo.
- ``POST /register``    → delega en ``AuthService.register_pending_user``,
                          luego coordina con ``OtpService``.
                          Si el envío OTP falla hace rollback vía
                          ``AuthService.delete_user``.
- ``POST /verify-otp``  → verifica código OTP, activa cuenta y emite tokens
                          vía ``AuthService.activate_user_and_issue_tokens``.
- ``POST /resend-otp``  → reenvía OTP al email del usuario.

Códigos de error de dominio (ValueError) que maneja este módulo
---------------------------------------------------------------
``EMAIL_PASSWORD_INCORRECT``      → 401
``USER_INACTIVE``                 → 403  (login) / 401 (refresh)
``REFRESH_TOKEN_EXPIRED``         → 401
``REFRESH_TOKEN_INVALID``         → 401
``USER_NOT_FOUND``                → 401 (refresh) / 404 (otp)
``EMAIL_ALREADY_REGISTERED``      → 409
``STUDENT_ROLE_NOT_CONFIGURED``   → 500
``ROLE_NOT_FOUND``                → 400

Nota sobre ``User.id`` y el guard ``if user.id is None``
---------------------------------------------------------
La entidad de dominio ``User`` declara ``id: UUID | None`` para representar
usuarios aún no persistidos (antes de hacer ``save_sync``).  Tras la llamada
a ``save_sync`` el repositorio asigna el UUID generado por la BD, pero el
type checker no puede inferir esa garantía de forma estática.  Por ello,
en cualquier punto donde ``user.id`` se pasa a una función que espera ``UUID``
(no ``UUID | None``) se añade un guard explícito que, en el caso improbable
de que el repositorio falle en asignar el id, retorna un error claro en lugar
de propagar un ``TypeError`` críptico.  La solución estructural definitiva
sería separar la entidad en ``PendingUser`` (sin id) y ``User`` (con id
garantizado), pero eso requiere una refactorización mayor del dominio.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_auth_service, get_current_token
from app.api.dependencies.otp import get_otp_service
from app.api.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RefreshTokenRequest,
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
from app.application.services.auth_service import AuthService, TokenPair
from app.application.services.otp_service import OtpService
from app.core.security import (
    TokenExpiredError,
    TokenInvalidError,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    validate_token,
)
from app.core.token_blacklist import add_token_to_blacklist, is_token_blacklisted

router = APIRouter()

# Expresión regular para validación básica de formato de email.
# No pretende cubrir el estándar RFC 5321 completo — solo rechaza
# casos claramente inválidos antes de consultar la BD.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _validate_login_fields(email: str, password: str) -> None:
    """Valida presencia y formato de las credenciales de login.

    Se ejecuta antes de cualquier consulta a la BD para devolver errores
    descriptivos al cliente sin coste de red.

    Args:
        email:    Email ya normalizado (strip aplicado).
        password: Contraseña ya normalizada (strip aplicado).

    Raises:
        HTTPException 400: Si algún campo está vacío o el email tiene
                           formato inválido.
    """
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
    if not _EMAIL_RE.match(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El formato del correo electrónico no es válido",
        )


def _pair_to_response(pair: TokenPair) -> TokenResponse:
    """Convierte un TokenPair al schema de respuesta HTTP."""
    return TokenResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
    )


def _decode_refresh_or_401(token: str) -> dict:
    """Decodifica un refresh token o lanza 401 si expiró o es inválido."""
    try:
        return decode_refresh_token(token)
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Inicia sesión con email y contraseña.

    Retorna un access token JWT y, si está habilitado, un refresh token.
    El access token debe enviarse en el header `Authorization: Bearer <token>`
    en todas las peticiones protegidas.

    - **400** — campo vacío o email con formato inválido.
    - **401** — credenciales incorrectas.
    - **403** — cuenta desactivada.
    """
    email = (credentials.email or "").strip()
    password = (credentials.password or "").strip()
    _validate_login_fields(email, password)

    try:
        pair = auth_service.authenticate(email, password)
    except ValueError as e:
        code = str(e)
        if code == "EMAIL_PASSWORD_INCORRECT":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if code == "USER_INACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo",
            )
        raise

    return _pair_to_response(pair)


@router.post("/logout", response_model=LogoutResponse)
def logout(token: str = Depends(get_current_token)) -> LogoutResponse:
    """Cierra la sesión invalidando el token actual.

    El token queda revocado de inmediato y no puede reutilizarse,
    aunque no haya expirado aún.  Requiere `Authorization: Bearer <token>`.
    """
    add_token_to_blacklist(token)
    return LogoutResponse(message="Sesión cerrada exitosamente")


@router.get("/me")
def get_current_user_info(token: str = Depends(get_current_token)) -> dict:
    """Retorna los datos básicos del usuario autenticado.

    Extrae la información del token sin consultar la base de datos.
    Útil para que el cliente verifique el estado de la sesión.
    Requiere `Authorization: Bearer <token>`.

    - **401** — token inválido o expirado.
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
def refresh_access_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Renueva el access token usando un refresh token válido.

    El refresh token anterior queda invalidado al completarse la operación
    (rotación de tokens). El nuevo par de tokens reemplaza al anterior.

    - **401** — refresh token revocado, expirado, inválido,
      o usuario no encontrado / desactivado.
    """
    if is_token_blacklisted(request.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token ha sido revocado. Inicie sesión nuevamente.",
                "error_code": "REFRESH_TOKEN_REVOKED",
                "redirect_to_login": True,
            },
        )

    # La decodificación puede lanzar TokenExpiredError / TokenInvalidError —
    # _decode_refresh_or_401 los traduce a HTTP 401 antes de llegar al servicio.
    payload = _decode_refresh_or_401(request.refresh_token)

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": "Refresh token no contiene ID de usuario.",
                "error_code": "REFRESH_TOKEN_INVALID",
                "redirect_to_login": True,
            },
        )

    try:
        pair = auth_service.refresh_tokens(user_id)
    except ValueError as e:
        code = str(e)
        _REFRESH_ERROR_MAP = {
            "USER_NOT_FOUND": "Usuario no encontrado.",
            "USER_INACTIVE":  "Usuario inactivo.",
        }
        message = _REFRESH_ERROR_MAP.get(code, "Error inesperado al renovar sesión.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "message": message,
                "error_code": code,
                "redirect_to_login": True,
            },
        )

    # Rotación: invalidar refresh token anterior una vez confirmado el éxito.
    add_token_to_blacklist(request.refresh_token)
    return _pair_to_response(pair)


@router.post("/validate", response_model=TokenValidationResponse)
def validate_access_token(request: TokenValidationRequest) -> TokenValidationResponse:
    """Comprueba si un access token es válido y no ha expirado.

    No renueva el token ni requiere autenticación previa. Retorna el estado
    del token junto con la causa si no es utilizable (`expired`, `revoked`,
    `invalid`). Útil para que el cliente decida si debe refrescar la sesión.
    """
    if is_token_blacklisted(request.token):
        return TokenValidationResponse(
            valid=False,
            expired=False,
            error="TOKEN_REVOKED",
            message="Token ha sido revocado",
        )

    is_valid, error_message = validate_token(request.token)

    if is_valid:
        return TokenValidationResponse(valid=True, message="Token es válido")

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
    auth_service: AuthService = Depends(get_auth_service),
    otp_service: OtpService = Depends(get_otp_service),
) -> OtpSentResponse:
    """Registra un nuevo usuario y envía un código de verificación por email.

    La cuenta queda inactiva hasta completar la verificación en `/verify-otp`.
    Si no se indica rol, se asigna **Student** por defecto.

    - **409** — el email ya está registrado y activo.
    - **400** — el rol indicado no existe.
    - **500** — error interno de configuración o persistencia.
    - **502** — no se pudo enviar el correo de verificación.
    """
    try:
        user = auth_service.register_pending_user(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role_id=data.role_id,
        )
    except ValueError as e:
        code = str(e)
        if code == "EMAIL_ALREADY_REGISTERED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado",
            )
        if code == "STUDENT_ROLE_NOT_CONFIGURED":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No existe el rol Student configurado en el sistema",
            )
        if code == "ROLE_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol indicado no existe",
            )
        raise

    # Guard: User.id es UUID | None en el dominio para representar entidades
    # aún no persistidas.  Tras save_sync el repositorio debe haber asignado
    # el UUID generado por la BD.  Si por algún motivo no lo hizo (bug en el
    # adaptador), fallamos aquí con un 500 claro en lugar de propagar un
    # TypeError críptico al intentar pasar None donde se espera UUID.
    if user.id is None:
        auth_service.delete_user(user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar el usuario",
        )

    try:
        await otp_service.generate_and_send(user_id=user.id, email=user.email)
    except Exception as e:
        # El envío falló: eliminar el usuario para no dejar un registro
        # huérfano con is_active=False que bloquee futuros re-registros.
        auth_service.delete_user(user)
        print(f"[ERROR] /register — fallo al enviar OTP a {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo enviar el correo de verificación. Intenta de nuevo.",
        )

    return OtpSentResponse()


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(
    data: VerifyOtpRequest,
    auth_service: AuthService = Depends(get_auth_service),
    otp_service: OtpService = Depends(get_otp_service),
) -> TokenResponse:
    """Verifica el código OTP y activa la cuenta del usuario.

    Si el código es válido, la cuenta queda activa y se retornan tokens JWT
    listos para usar, equivalentes a los de un login exitoso.

    - **404** — el email no existe.
    - **400** — código inválido o expirado.
    - **500** — error interno al activar la cuenta.
    """
    user = auth_service.get_user_by_email(data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Guard: User.id es UUID | None en el dominio para representar entidades
    # aún no persistidas.  Un usuario recuperado de la BD siempre tiene id,
    # pero el type checker no puede inferirlo a partir de UUID | None.
    # El guard debe ir ANTES de cualquier llamada que espere UUID (como
    # otp_service.verify) para que el análisis de flujo estreche el tipo
    # de user.id a UUID en las líneas siguientes.
    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el usuario",
        )

    if not otp_service.verify(user_id=user.id, code=data.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido o expirado",
        )

    try:
        pair = auth_service.activate_user_and_issue_tokens(user)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al activar la cuenta del usuario",
        )

    return _pair_to_response(pair)


@router.post("/resend-otp", response_model=OtpSentResponse)
async def resend_otp(
    data: ResendOtpRequest,
    auth_service: AuthService = Depends(get_auth_service),
    otp_service: OtpService = Depends(get_otp_service),
) -> OtpSentResponse:
    """Reenvía el código de verificación al correo del usuario.

    Invalida el código anterior y genera uno nuevo. Solo es posible si
    ha transcurrido el tiempo mínimo entre reenvíos (`otp_resend_cooldown`).

    - **404** — el email no existe.
    - **400** — no hay código activo para el usuario.
    - **429** — debe esperar antes de solicitar un nuevo código.
    """
    user = auth_service.get_user_by_email(data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Guard: misma razón que en /register y /verify-otp.  Un usuario
    # recuperado de la BD siempre tendrá id, pero el type checker no puede
    # inferirlo a partir de UUID | None.
    if user.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al verificar el usuario",
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