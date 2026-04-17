from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template

import aiosmtplib

from app.application.ports.email_sender import EmailSenderPort
from app.core.config import settings

_TEMPLATE_PATH = Path(__file__).parents[2] / "templates" / "email" / "otp_template.html"


class SmtpEmailSender(EmailSenderPort):
    """Adaptador SMTP — funciona con Mailpit (local) y cualquier SMTP genérico."""

    async def send_otp(self, to: str, code: str, expire_minutes: int) -> None:
        html = Template(_TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(
            code=code,
            expire_minutes=expire_minutes,
        )

        message = MIMEMultipart("alternative")
        message["Subject"] = "Tu código de verificación"
        message["From"] = settings.mail_from
        message["To"] = to
        message.attach(MIMEText(html, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.mail_host,
            port=settings.mail_port,
            username=settings.mail_username or None,
            password=settings.mail_password or None,
            use_tls=False,
            start_tls=settings.mail_start_tls,
        )
