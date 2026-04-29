from pathlib import Path
from string import Template
import resend
from app.application.ports.email_sender import EmailSenderPort
from app.core.config import settings

_TEMPLATE_PATH = Path(__file__).parents[2] / "templates" / "email" / "otp_template.html"

class ResendEmailSender(EmailSenderPort):
    async def send_otp(self, to: str, code: str, expire_minutes: int) -> None:
        resend.api_key = settings.resend_api_key

        html = Template(_TEMPLATE_PATH.read_text(encoding="utf-8")).substitute(
            code=code,
            expire_minutes=expire_minutes,
        )
        resend.Emails.send({
            "from": settings.mail_from,
            "to": to,
            "subject": "Tu código de verificación",
            "html": html,
        })