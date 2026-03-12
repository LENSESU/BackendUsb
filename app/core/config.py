"""Configuración de la aplicación mediante variables de entorno."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración cargada desde entorno y .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base de datos (si no se define DATABASE_URL se construye desde POSTGRES_*)
    database_url: str | None = None
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "app_db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url_sync(self) -> str:
        """URL de conexión PostgreSQL síncrona (Alembic, migraciones)."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Entorno
    environment: Literal["development", "staging", "production"] = "development"

    # Si es False, no se ejecutan migraciones al arranque (útil en tests sin BD)
    run_migrations_on_startup: bool = True

    # Autenticación JWT
    jwt_secret_key: str = "dev-secret-key-CHANGE-IN-PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1 hora
    refresh_token_expire_days: int = 7  # 7 días
    # Si es True, el login devuelve también refresh_token
    use_refresh_tokens: bool = True

    # SMTP Server (Local) - OTP
    mail_host: str = "localhost"
    mail_port: int = 1025
    mail_from: str = "noreply@app.local"
    mail_username: str = ""
    mail_password: str = ""
    otp_expire_minutes: int = 2
    otp_resend_cooldown_seconds: int = 15

    # Whitelist domains
    allowed_email_domains: list[str] = ["correo.usbcali.edu.co", "usbcali.edu.co"]

    # Google Cloud Storage
    gcs_enabled: bool = False
    gcs_project_id: str | None = None
    gcs_bucket_name: str = ""
    gcs_evidence_prefix: str = "incidents/evidence"
    gcs_make_public: bool = False


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración cacheada."""
    return Settings()


# Instancia global para uso en app y Alembic
settings = get_settings()
