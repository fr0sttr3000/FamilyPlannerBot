"""Базовый класс для всех SQLAlchemy ORM-моделей."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс декларативных моделей."""
    pass
