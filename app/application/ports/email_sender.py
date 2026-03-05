from abc import ABC, abstractmethod


class EmailSenderPort(ABC):
    """Puerto: contrato para envío de correos.
    La capa de aplicación solo conoce esta interfaz."""

    @abstractmethod
    async def send_otp(self, to: str, code: str, expire_minutes: int) -> None:
        """Envía el código OTP al destinatario."""
        ...
