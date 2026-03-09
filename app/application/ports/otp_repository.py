from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.otp import Otp


class OtpRepositoryPort(ABC):
    """Contrato que debe cumplir cualquier adaptador de persistencia de OTPs."""

    @abstractmethod
    def save(self, otp: Otp) -> Otp:
        """Persiste un nuevo OTP."""
        ...

    @abstractmethod
    def find_active_by_user_id(self, user_id: UUID) -> Otp | None:
        """Retorna el OTP activo (deleted_at IS NULL) de un usuario, o None."""
        ...

    @abstractmethod
    def soft_delete(self, otp_id: UUID) -> None:
        """Marca el OTP como consumido (deleted_at = NOW(), updated_at = NOW())."""
        ...
