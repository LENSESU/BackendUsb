"""Caso de uso: generación y verificación de OTPs para activación de cuenta."""

import asyncio
import secrets
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from uuid import UUID

import aiosmtplib

from app.application.ports.otp_repository import OtpRepositoryPort
from app.core.config import settings
from app.domain.entities.otp import Otp


async def _send_otp_email(email: str, code: str) -> None:
    message = MIMEText(
        f"Tu código de verificación es: {code}\n\n"
        f"Expira en {settings.otp_expire_minutes} minutos.\n"
        "Si no solicitaste este código, ignora este mensaje.",
        "plain",
    )
    message["Subject"] = "Tu código de verificación"
    message["From"] = settings.mail_from
    message["To"] = email

    await aiosmtplib.send(
        message,
        hostname=settings.mail_host,
        port=settings.mail_port,
        username=settings.mail_username or None,
        password=settings.mail_password or None,
        use_tls=False,
        start_tls=False,
    )


class OtpService:
    """Servicio de aplicación para OTPs. Orquesta dominio y puertos."""

    def __init__(self, repository: OtpRepositoryPort) -> None:
        self._repository = repository

    def generate_and_send(self, user_id: UUID, email: str) -> None:
        # Invalidar OTP activo previo si existe
        existing = self._repository.find_active_by_user_id(user_id)
        if existing and existing.id is not None:
            self._repository.soft_delete(existing.id)

        # Generar código de 6 dígitos criptográficamente seguro
        code = str(secrets.randbelow(10**6)).zfill(6)
        otp = Otp(id=None, user_id=user_id, code=code)
        self._repository.save(otp)

        # Enviar email
        asyncio.run(_send_otp_email(email, code))

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
            return False

        if otp.code != code:
            return False

        if otp.id is not None:
            self._repository.soft_delete(otp.id)

        return True
