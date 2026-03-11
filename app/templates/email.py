"""Notificaciones por email basadas en plantillas HTML."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from string import Template

import aiosmtplib

from app.core.config import settings

_VERIFICATION_TEMPLATE_PATH = (
    Path(__file__).parent / "email" / "verification_code_template.html"
)


async def send_verification_code(to_email: str, code: str) -> None:
    """Envía un código de verificación usando un template HTML."""
    html = Template(_VERIFICATION_TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(
        code=code,
    )

    message = MIMEMultipart("alternative")
    message["Subject"] = "Tu código de verificación"
    message["From"] = settings.mail_from
    message["To"] = to_email
    message.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        message,
        hostname=settings.mail_host,
        port=settings.mail_port,
        username=settings.mail_username or None,
        password=settings.mail_password or None,
        use_tls=False,
        start_tls=False,
    )
