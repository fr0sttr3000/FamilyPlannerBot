"""Сервис административных данных (US-23). Бизнес-логика без зависимости от Telegram."""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import Event
from app.db.models.reminder import REMINDER_STATUS_PENDING, Reminder
from app.db.models.task import Task

logger = logging.getLogger(__name__)

ADMIN_UPCOMING_REMINDERS_LIMIT = 5
ADMIN_WEEK_DAYS = 7


@dataclass
class AdminOverview:
    """Сводка состояния бота для /adminoverview."""

    generated_at: datetime
    active_tasks_count: int
    upcoming_reminders: list[Reminder] = field(default_factory=list)
    week_events: list[Event] = field(default_factory=list)


class AdminService:
    """Агрегация административной статистики (US-23).

    Содержит только чтение данных — никаких мутаций.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_overview(self) -> AdminOverview:
        """Собрать сводку: активные задачи, ближайшие напоминания, события на неделю.

        Returns:
            AdminOverview с агрегированными данными.
        """
        now = datetime.now(timezone.utc)
        week_end = now + timedelta(days=ADMIN_WEEK_DAYS)

        # 1. Количество активных задач
        tasks_count_result = await self._session.execute(
            select(func.count(Task.id)).where(
                Task.deleted_at.is_(None),
                Task.completed_at.is_(None),
            )
        )
        active_tasks_count: int = tasks_count_result.scalar_one()

        # 2. Ближайшие 5 напоминаний
        reminders_result = await self._session.execute(
            select(Reminder)
            .where(
                Reminder.status == REMINDER_STATUS_PENDING,
                Reminder.deleted_at.is_(None),
                Reminder.scheduled_at >= now,
            )
            .order_by(Reminder.scheduled_at.asc())
            .limit(ADMIN_UPCOMING_REMINDERS_LIMIT)
        )
        upcoming_reminders = list(reminders_result.scalars().all())

        # 3. События на ближайшую неделю
        events_result = await self._session.execute(
            select(Event)
            .where(
                Event.deleted_at.is_(None),
                Event.event_date >= now.date(),
                Event.event_date <= week_end.date(),
            )
            .order_by(Event.event_date.asc())
        )
        week_events = list(events_result.scalars().all())

        logger.info(
            "admin_overview: tasks=%d reminders=%d events=%d",
            active_tasks_count, len(upcoming_reminders), len(week_events),
        )
        return AdminOverview(
            generated_at=now,
            active_tasks_count=active_tasks_count,
            upcoming_reminders=upcoming_reminders,
            week_events=week_events,
        )
