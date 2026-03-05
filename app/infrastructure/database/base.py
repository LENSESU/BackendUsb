"""Base declarativa de SQLAlchemy para todos los modelos ORM."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Clase base para modelos de la capa de persistencia."""

    pass
