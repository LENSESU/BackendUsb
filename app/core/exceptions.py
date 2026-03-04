"""Excepciones de dominio/aplicación para manejo centralizado en la API."""


class AppError(Exception):
    """Base para errores de la aplicación con código HTTP y mensaje."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidCredentialsError(AppError):
    """Credenciales incorrectas (login)."""

    def __init__(self, message: str = "Credenciales inválidas") -> None:
        super().__init__(message, status_code=401)


class UserAlreadyExistsError(AppError):
    """El usuario ya existe (registro con email duplicado)."""

    def __init__(self, message: str = "El usuario ya existe") -> None:
        super().__init__(message, status_code=400)


class NotFoundError(AppError):
    """Recurso no encontrado."""

    def __init__(self, message: str = "Recurso no encontrado") -> None:
        super().__init__(message, status_code=404)


class ValidationError(AppError):
    """Error de validación de negocio."""

    def __init__(self, message: str, status_code: int = 422) -> None:
        super().__init__(message, status_code=status_code)
