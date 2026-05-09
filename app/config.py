"""Конфигурация приложения через pydantic-settings.

Все настройки загружаются из переменных окружения (файл .env).
Секреты никогда не хардкодятся в коде.
"""
import logging
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Читаются из .env файла."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str
    owner_id: int

    # База данных
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "familybot"
    db_user: str = "familybot"
    db_password: str

    # Авторизация
    allowed_users: frozenset[int]

    # Конфигурация
    timezone: str = "Europe/Moscow"
    log_level: str = "INFO"

    @field_validator("allowed_users", mode="before")
    @classmethod
    def parse_allowed_users(cls, v: str | frozenset) -> frozenset[int]:
        """Парсит строку '123,456,789' в frozenset целых чисел."""
        if isinstance(v, frozenset):
            return v
        return frozenset(int(uid.strip()) for uid in str(v).split(",") if uid.strip())

    @property
    def database_url(self) -> str:
        """Async URL для SQLAlchemy + asyncpg."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL для Alembic и APScheduler JobStore."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает единственный экземпляр настроек (singleton)."""
    return Settings()


settings = get_settings()

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
