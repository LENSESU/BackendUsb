"""Caso de uso: autenticación por email/password."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.application.ports import UserRepositoryPort
from app.core.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.domain.entities import User, UserRole

# Configuración de Argon2id con parámetros algo más ligeros para desarrollo.
_ph = PasswordHasher(
    time_cost=2,  # iteraciones (por defecto suele ser 3)
    memory_cost=51200,  # KB (~50 MB)
    parallelism=2,
)


class AuthService:
    """Servicio de aplicación para autenticación.

    Regla de negocio: si el usuario no existe al intentar autenticarse,
    se crea automáticamente con el email y password proporcionados.
    """

    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._user_repository = user_repository

    def _hash_password(self, plain_password: str) -> str:
        """Genera un hash Argon2id del password en texto plano."""
        return _ph.hash(plain_password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica un password en texto plano contra un hash Argon2id almacenado."""
        try:
            return _ph.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False

    async def register(
        self,
        email: str,
        password: str,
        name: str | None = None,
    ) -> User:
        """Registra un usuario nuevo.

        Falla si el usuario ya existe.
        """
        existing = await self._user_repository.get_by_email(email=email)
        if existing is not None:
            raise UserAlreadyExistsError()

        password_hash = self._hash_password(password)
        user = User(
            email=email.strip(),
            password_hash=password_hash,
            name=name,
            role=UserRole.STUDENT,
        )
        return await self._user_repository.save(user)

    async def login_or_register(self, email: str, password: str) -> User:
        """Autentica o registra un usuario."""
        existing = await self._user_repository.get_by_email(email=email)

        if existing is not None:
            if not self._verify_password(password, existing.password_hash):
                raise InvalidCredentialsError()
            return existing

        password_hash = self._hash_password(password)
        user = User(
            email=email.strip(),
            password_hash=password_hash,
            role=UserRole.STUDENT,
        )
        return await self._user_repository.save(user)
