"""APScheduler setup — Sprint 2: SQLAlchemy JobStore + Production Jobs."""
import logging
from datetime import datetime, timezone

import pytz
from aiogram import Bot
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import settings
from app.db.models.event import Event
from app.db.models.reminder import REMINDER_STATUS_FIRED, REMINDER_STATUS_PENDING, Reminder
from app.db.models.task import Task
from app.db.repositories.reminder_repo import ReminderRepository
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

_bot: Bot | None = None


async def _deliver_pending(label: str) -> int:
    """Доставить все pending-напоминания. Возвращает количество доставленных."""
    count = 0
    async with async_session_factory() as session:
        repo = ReminderRepository(session)
        due = await repo.get_due()
        for reminder in due:
            try:
                await _bot.send_message(reminder.user_id, f"⏰ Напоминание:\n{reminder.text}")
                reminder.status = REMINDER_STATUS_FIRED
                reminder.fired_at = datetime.now(timezone.utc)
                count += 1
            except Exception:
                logger.exception("[%s] Ошибка доставки reminder_id=%d", label, reminder.id)
        if count:
            await session.commit()
    return count


async def deliver_reminders() -> None:
    """Job: доставка напоминаний каждую минуту."""
    await _deliver_pending("deliver_reminders")


async def watchdog() -> None:
    """Job: авторецовери пропущенных напоминаний (каждые 10 мин)."""
    count = await _deliver_pending("watchdog")
    if count:
        logger.warning("watchdog: исправлено %d пропущенных напоминаний", count)


async def morning_digest() -> None:
    """Job: утреннее уведомление о событиях и задачах (08:00)."""
    tz = pytz.timezone(settings.timezone)
    today = datetime.now(tz).date()

    async with async_session_factory() as session:
        events_result = await session.execute(
            select(Event).where(Event.event_date == today, Event.deleted_at.is_(None))
        )
        events = list(events_result.scalars().all())

        tasks_result = await session.execute(
            select(Task).where(Task.deleted_at.is_(None), Task.completed_at.is_(None))
        )
        tasks = list(tasks_result.scalars().all())

    if not events and not tasks:
        return

    lines = [f"<b>Доброе утро! Сводка на {today.strftime('%d.%m.%Y')}:</b>"]
    if events:
        lines.append("\n<b>События сегодня:</b>")
        lines.extend(f"• {e.text}" for e in events)
    if tasks:
        lines.append("\n<b>Активные задачи:</b>")
        lines.extend(f"• {t.text}" for t in tasks)

    message = "\n".join(lines)
    for user_id in settings.allowed_users:
        try:
            await _bot.send_message(user_id, message)
        except Exception:
            logger.warning("morning_digest: ошибка отправки user_id=%d", user_id)


async def heartbeat() -> None:
    """Job: сигнал о работоспособности бота (каждые 5 мин)."""
    logger.info("heartbeat: bot alive")


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Создать AsyncIOScheduler с SQLAlchemy JobStore и 4 production jobs."""
    global _bot
    _bot = bot

    jobstores = {"default": SQLAlchemyJobStore(url=settings.database_url_sync)}
    job_defaults = {"coalesce": True, "max_instances": 1, "misfire_grace_time": 60}

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        job_defaults=job_defaults,
        timezone=settings.timezone,
    )

    scheduler.add_job(deliver_reminders, "interval", minutes=1, id="deliver_reminders", replace_existing=True)
    scheduler.add_job(morning_digest, "cron", hour=8, minute=0, id="morning_digest", replace_existing=True)
    scheduler.add_job(heartbeat, "interval", minutes=5, id="heartbeat", replace_existing=True)
    scheduler.add_job(watchdog, "interval", minutes=10, id="watchdog", replace_existing=True)

    logger.info("APScheduler создан: SQLAlchemy JobStore, 4 jobs зарегистрированы")
    return scheduler
