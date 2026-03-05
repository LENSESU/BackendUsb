"""Envío de correos vía SMTP (códigos de verificación, etc.)."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_verification_code(to_email: str, code: str) -> bool:
    """
    Envía el código de verificación por email usando SMTP.

    Si SMTP no está habilitado o falla el envío, registra el error y devuelve False.
    El código no se expone en logs en producción.

    Args:
        to_email: Dirección de destino.
        code: Código de 6 dígitos a incluir en el mensaje.

    Returns:
        True si el correo se envió correctamente, False en caso contrario.
    """
    if not settings.smtp_enabled:
        logger.debug(
            "SMTP deshabilitado: no se envía código a %s (configura SMTP_ENABLED=true)",
            to_email,
        )
        return False

    subject = "Tu código de verificación"
    body = f"""Hola,

Tu código de verificación es: {code}

Es válido durante 10 minutos. No lo compartas con nadie.

Si no solicitaste este código, puedes ignorar este mensaje.
"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())
        logger.info("Código de verificación enviado a %s", to_email)
        return True
    except Exception as e:
        logger.exception("Error al enviar código por email a %s: %s", to_email, e)
        return False
