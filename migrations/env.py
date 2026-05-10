"""Alembic env.py — конфигурация окружения миграций."""
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Добавляем корень проекта в sys.path для импорта моделей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# noqa: E402 — импорты после настройки sys.path
from app.db.models.base import Base  # noqa: E402
import app.db.models  # noqa: E402, F401 — регистрация всех моделей

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_url() -> str:
    """Получить URL БД из переменных окружения."""
    from app.config import settings
    return settings.database_url_sync


def run_migrations_offline() -> None:
    """Запустить миграции в offline-режиме (без подключения к БД)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запустить миграции в online-режиме (с подключением к БД)."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
