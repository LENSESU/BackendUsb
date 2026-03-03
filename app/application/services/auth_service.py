"""Caso de uso: autenticación por email/password."""

from uuid import uuid4

from passlib.context import CryptContext

from app.application.ports import UserRepositoryPort
from app.domain.entities import User

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Servicio de aplicación para autenticación.

    Regla de negocio: si el usuario no existe al intentar autenticarse,
    se crea automáticamente con el email y password proporcionados.
    """

    def __init__(self, user_repository: UserRepositoryPort) -> None:
        self._user_repository = user_repository

    def _hash_password(self, plain_password: str) -> str:
        return _pwd_context.hash(plain_password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return _pwd_context.verify(plain_password, hashed_password)

    async def register(self, email: str, password: str, name: str | None = None) -> User:
        """Registra un usuario nuevo.

        Falla si el usuario ya existe.
        """
        existing = await self._user_repository.get_by_email(email=email)
        if existing is not None:
            msg = "El usuario ya existe"
            raise ValueError(msg)

        password_hash = self._hash_password(password)
        user = User(
            id=uuid4(),
            email=email.strip(),
            password_hash=password_hash,
            name=name,
        )
        return await self._user_repository.save(user)

    async def login_or_register(self, email: str, password: str) -> User:
        """Autentica o registra un usuario."""
        existing = await self._user_repository.get_by_email(email=email)

        if existing is not None:
            if not self._verify_password(password, existing.password_hash):
                msg = "Credenciales inválidas"
                raise ValueError(msg)
            return existing

        password_hash = self._hash_password(password)
        user = User(id=uuid4(), email=email.strip(), password_hash=password_hash)
        return await self._user_repository.save(user)

