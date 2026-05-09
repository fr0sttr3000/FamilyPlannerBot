"""APScheduler setup — Sprint 1 заглушка.

В Sprint 1 создаётся инфраструктура планировщика без реальных jobs.
В Sprint 2 добавляются:
- deliver_reminder job (доставка напоминаний)
- morning_digest job (утреннее уведомление о событиях)
- heartbeat + watchdog jobs (мониторинг)
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    """Создать и настроить AsyncIOScheduler.

    Sprint 1: планировщик стартует, но без jobs.
    Jobs добавляются в Sprint 2 через scheduler.add_job().
    """
    scheduler = AsyncIOScheduler(
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        },
        timezone=settings.timezone,
    )
    logger.info("APScheduler создан (Sprint 1: без jobs, доставка — Sprint 2)")
    return scheduler
