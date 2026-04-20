"""Caso de uso: autenticación, registro y gestión de tokens."""

from dataclasses import dataclass
from uuid import UUID

from app.application.ports.user_repository import UserRepositoryPort
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.domain.entities import User


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str | None
    expires_in: int


class AuthService:
    """Orquesta autenticación y emisión de tokens. Sin conocimiento de HTTP."""

    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._users = user_repository

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _build_token_pair(self, user: User) -> TokenPair:
        """Construye access + refresh token para un usuario ya validado."""
        token_data: dict = {
            "sub": str(user.id),
            "email": user.email,
            "role_id": str(user.role_id),
        }
        role_name = self._users.get_role_name_by_id(user.role_id)
        if role_name:
            token_data["role_name"] = role_name

        access_token = create_access_token(data=token_data)
        refresh_token = (
            create_refresh_token(data={"sub": str(user.id)})
            if settings.use_refresh_tokens
            else None
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    # ------------------------------------------------------------------
    # Casos de uso
    # ------------------------------------------------------------------

    def authenticate(self, email: str, password: str) -> TokenPair:
        """
        Valida credenciales y retorna tokens.

        Raises:
            ValueError("EMAIL_PASSWORD_INCORRECT"): credenciales inválidas.
            ValueError("USER_INACTIVE"): cuenta desactivada.
        """
        user = self._users.get_by_email_sync(email)

        # Mismo mensaje para email y password — evita user enumeration
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("EMAIL_PASSWORD_INCORRECT")

        if not user.is_active:
            raise ValueError("USER_INACTIVE")

        return self._build_token_pair(user)

    def refresh_tokens(self, user_id: str) -> TokenPair:
        """
        Genera nuevos tokens para un user_id ya validado por el router.

        Raises:
            ValueError("USER_NOT_FOUND"): usuario no existe.
            ValueError("USER_INACTIVE"): cuenta desactivada.
        """
        try:
            uid = UUID(user_id)
        except ValueError:
            raise ValueError("USER_NOT_FOUND")

        basic = self._users.get_by_id(uid)
        if basic is None:
            raise ValueError("USER_NOT_FOUND")

        # Reconstruir User mínimo para _build_token_pair
        # get_by_id solo retorna UserBasicData — necesitamos role_id
        # por eso hacemos get_by_email_sync con el email que ya tenemos
        user = self._users.get_by_email_sync(basic.email)
        if user is None:
            raise ValueError("USER_NOT_FOUND")
        if not user.is_active:
            raise ValueError("USER_INACTIVE")

        return self._build_token_pair(user)

    def activate_user_and_issue_tokens(self, user: User) -> TokenPair:
        """Activa la cuenta y emite tokens. Persiste is_active=True."""
        user.is_active = True
        self._users.save_sync(user)
        return self._build_token_pair(user)

    def register_pending_user(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password_hash: str,
        role_id: UUID | None,
    ) -> User:
        """
        Valida y crea un usuario inactivo listo para verificación OTP.

        Lógica:
        - Si el email ya existe y está activo  → ValueError("EMAIL_ALREADY_REGISTERED")
        - Si el email ya existe e inactivo     → se elimina para permitir re-registro
        - Si role_id es None                   → asigna rol "Student" por defecto
        - Si role_id viene                     → valida que exista
        - Crea el User con is_active=False

        El caller (router) es responsable de llamar al OTP service después
        y de hacer rollback (delete) si el envío falla.

        Args:
            first_name:     Nombre del usuario.
            last_name:      Apellido del usuario.
            email:          Email único del usuario.
            password_hash:  Hash de la contraseña ya procesado.
            role_id:        UUID del rol deseado, o None para usar "Student".

        Returns:
            User persistido con is_active=False.

        Raises:
            ValueError("EMAIL_ALREADY_REGISTERED"): email activo ya existe.
            ValueError("STUDENT_ROLE_NOT_CONFIGURED"): rol Student no existe en BD.
            ValueError("ROLE_NOT_FOUND"): role_id indicado no existe en BD.
        """
        # 1. Verificar email duplicado
        existing = self._users.get_by_email_sync(email)
        if existing is not None:
            if existing.is_active:
                raise ValueError("EMAIL_ALREADY_REGISTERED")
            # Re-registro: limpiar usuario inactivo anterior
            self._users.delete_sync(existing)

        # 2. Resolver rol
        resolved_role_id: UUID
        if role_id is None:
            student_role = self._users.get_role_by_name("Student")
            if student_role is None:
                raise ValueError("STUDENT_ROLE_NOT_CONFIGURED")
            resolved_role_id = student_role.id  # type: ignore[assignment]
        else:
            role = self._users.get_role_by_id(role_id)
            if role is None:
                raise ValueError("ROLE_NOT_FOUND")
            resolved_role_id = role_id

        # 3. Crear y persistir usuario inactivo
        user = User(
            id=None,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email,
            password_hash=password_hash,
            role_id=resolved_role_id,
            is_active=False,
        )
        return self._users.save_sync(user)

    def get_user_by_email(self, email: str) -> User | None:
        """Localiza un usuario por email. Fachada sobre el repositorio."""
        return self._users.get_by_email_sync(email)

    def delete_user(self, user: User) -> None:
        """Elimina un usuario. Usado para rollback post-fallo de OTP."""
        self._users.delete_sync(user)
