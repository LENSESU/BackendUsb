import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template

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

        async with aiosmtplib.SMTP(
            hostname=settings.mail_host,
            port=settings.mail_port,
            use_tls=False,          # conexión inicial en plano
        ) as smtp:
            if settings.mail_start_tls:
                await smtp.starttls()  # upgrade a TLS
            if settings.mail_username:
                await smtp.login(      # auth canal cifrado
                    settings.mail_username,
                    settings.mail_password,
                )
            await smtp.send_message(message)