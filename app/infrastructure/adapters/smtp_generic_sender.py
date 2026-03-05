from email.mime.text import MIMEText

import aiosmtplib

from app.application.ports.email_sender import EmailSenderPort
from app.core.config import settings


class SmtpEmailSender(EmailSenderPort):
    """Adaptador SMTP — funciona con Mailpit (local) y cualquier SMTP genérico."""

    async def send_otp(self, to: str, code: str, expire_minutes: int) -> None:
        message = MIMEText(
            f"Tu código de verificación es: {code}\n\n"
            f"Expira en {expire_minutes} minutos.\n"
            "Si no solicitaste este código, ignora este mensaje.",
            "plain",
        )
        message["Subject"] = "Tu código de verificación"
        message["From"] = settings.mail_from
        message["To"] = to

        await aiosmtplib.send(
            message,
            hostname=settings.mail_host,
            port=settings.mail_port,
            username=settings.mail_username or None,
            password=settings.mail_password or None,
            use_tls=False,
            start_tls=False,
        )
