from app.application.services.otp_service import OtpService
from app.infrastructure.adapters.smtp_generic_sender import SmtpEmailSender
from app.infrastructure.adapters.otp_repository import SqlOtpRepository


def get_otp_service() -> OtpService:
    return OtpService(
        repository=SqlOtpRepository(),
        email_sender=SmtpEmailSender(),
    )