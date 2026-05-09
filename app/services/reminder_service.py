"""Сервис напоминаний. Sprint 1: только CRUD (без APScheduler-доставки)."""
import logging
from dataclasses import dataclass
from datetime import datetime

import pytz

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.reminder import Reminder
from app.db.repositories.reminder_repo import ReminderRepository

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


@dataclass
class ReminderResult:
    """Результат операции с напоминанием."""

    success: bool
    reminder: Reminder | None = None
    error: str | None = None


class ReminderService:
    """Управление напоминаниями (Sprint 1: CRUD без доставки)."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = ReminderRepository(session)
        self._session = session

    def _parse_scheduled_at(self, date_str: str, time_str: str) -> datetime | None:
        """Парсит дату и время в timezone-aware datetime. Возвращает None при ошибке."""
        try:
            tz = pytz.timezone(settings.timezone)
            naive = datetime.strptime(f"{date_str} {time_str}", f"{DATE_FORMAT} {TIME_FORMAT}")
            return tz.localize(naive)
        except (ValueError, pytz.exceptions.UnknownTimeZoneError):
            return None

    async def create_reminder(
        self, user_id: int, date_str: str, time_str: str, text: str
    ) -> ReminderResult:
        """Создать напоминание. Валидирует дату/время и текст."""
        text = text.strip()
        if not text:
            return ReminderResult(success=False, error="Текст напоминания не может быть пустым.")

        scheduled_at = self._parse_scheduled_at(date_str, time_str)
        if scheduled_at is None:
            return ReminderResult(
                success=False,
                error=(
                    "Неверный формат даты или времени.\n"
                    "Пример: /addreminder 2026-05-10 14:30 Купить молоко"
                ),
            )

        reminder = Reminder(user_id=user_id, text=text, scheduled_at=scheduled_at)
        saved = await self._repo.save(reminder)
        await self._session.commit()
        logger.info("user=%d action=reminder_create reminder_id=%d", user_id, saved.id)
        return ReminderResult(success=True, reminder=saved)

    async def get_active_reminders(self, user_id: int) -> list[Reminder]:
        """Список активных напоминаний пользователя."""
        return await self._repo.get_active_for_user(user_id)

    async def delete_reminder(self, reminder_id: int, user_id: int) -> ReminderResult:
        """Soft delete напоминания. Проверяет владельца."""
        reminder = await self._repo.soft_delete(reminder_id, user_id)
        if reminder is None:
            return ReminderResult(
                success=False,
                error=f"Напоминание с ID {reminder_id} не найдено или вам не принадлежит.",
            )
        await self._session.commit()
        logger.info("user=%d action=reminder_delete reminder_id=%d", user_id, reminder_id)
        return ReminderResult(success=True, reminder=reminder)
