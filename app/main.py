"""Точка входа FamilyPlannerBot.

Инициализирует бота, регистрирует middleware и handlers,
применяет миграции Alembic, запускает APScheduler и polling.
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig

from app.bot.handlers import admin, calendar, notes, reminders, start, tasks
from app.bot.middlewares.auth import AuthMiddleware
from app.bot.middlewares.db import DBSessionMiddleware
from app.config import settings
from app.db.session import async_session_factory
from app.scheduler.reminder_scheduler import create_scheduler

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Применить все pending-миграции Alembic при старте."""
    try:
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_command.upgrade(alembic_cfg, "head")
        logger.info("Alembic миграции применены успешно")
    except Exception:
        logger.exception("Ошибка применения миграций Alembic")
        sys.exit(1)


def build_dispatcher() -> Dispatcher:
    """Создать Dispatcher и зарегистрировать middleware + routers."""
    dp = Dispatcher()

    # Middleware (порядок важен: сначала DB, затем Auth)
    dp.update.middleware(DBSessionMiddleware(async_session_factory))
    dp.update.middleware(AuthMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(tasks.router)
    dp.include_router(notes.router)
    dp.include_router(reminders.router)
    dp.include_router(calendar.router)
    dp.include_router(admin.router)

    return dp


async def main() -> None:
    """Главная async-функция запуска бота."""
    logger.info("Запуск FamilyPlannerBot...")

    # 1. Применить миграции
    run_migrations()

    # 2. Инициализировать бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # 3. Создать Dispatcher
    dp = build_dispatcher()

    # 4. Запустить планировщик
    scheduler = create_scheduler(bot)
    scheduler.start()
    logger.info("APScheduler запущен")

    # 5. Запустить polling
    try:
        logger.info("Запуск long polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
