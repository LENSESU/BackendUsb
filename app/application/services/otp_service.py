"""Caso de uso: generación y verificación de OTPs para activación de cuenta."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.application.ports.email_sender import EmailSenderPort
from app.application.ports.otp_repository import OtpRepositoryPort
from app.core.config import settings
from app.domain.entities.otp import Otp


class OtpService:
    def __init__(
        self,
        repository: OtpRepositoryPort,
        email_sender: EmailSenderPort,
    ) -> None:
        self._repository = repository
        self._email_sender = email_sender

    async def generate_and_send(self, user_id: UUID, email: str) -> None:
        existing = self._repository.find_active_by_user_id(user_id)
        if existing and existing.id is not None:
            self._repository.soft_delete(existing.id)

        code = str(secrets.randbelow(10**6)).zfill(6)
        self._repository.save(Otp(id=None, user_id=user_id, code=code))

        await self._email_sender.send_otp(email, code, settings.otp_expire_minutes)

    def verify(self, user_id: UUID, code: str) -> bool:
        otp = self._repository.find_active_by_user_id(user_id)
        if otp is None:
            return False

        if otp.created_at is None:
            return False

        expiry = otp.created_at.replace(tzinfo=UTC) + timedelta(
            minutes=settings.otp_expire_minutes
        )
        if datetime.now(UTC) > expiry:
            if otp.id is not None:
                self._repository.soft_delete(otp.id)
            return False

        if otp.code != code:
            return False

        if otp.id is not None:
            self._repository.soft_delete(otp.id)

        return True

    async def resend(self, user_id: UUID, email: str) -> None:
        """
        Reenvía un OTP invalidando el activo actual.

        Si no hay OTP activo, lanza error — el usuario debe registrarse primero.
        Si el OTP activo tiene menos de otp_resend_cooldown_seconds, lanza error
        con los segundos restantes para que el cliente pueda informar al usuario.

        Raises:
            ValueError: Si no hay OTP activo o el cooldown no ha pasado.
        """
        existing = self._repository.find_active_by_user_id(user_id)

        if existing is None:
            raise ValueError("No hay un OTP activo para este usuario")

        if existing.created_at is None:
            raise ValueError("OTP en estado inválido")

        # Cooldown
        elapsed = (
            datetime.now(UTC) - existing.created_at.replace(tzinfo=UTC)
        ).total_seconds()
        remaining = settings.otp_resend_cooldown_seconds - elapsed
        if remaining > 0:
            raise ValueError(
                f"Debes esperar {int(remaining) + 1} segundos antes de reenviar"
            )

        await self.generate_and_send(user_id=user_id, email=email)
