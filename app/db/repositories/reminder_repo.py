"""Репозиторий напоминаний."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.reminder import REMINDER_STATUS_PENDING, Reminder
from app.db.repositories.base import BaseRepository

ACTIVE_REMINDERS_LIMIT = 50


class ReminderRepository(BaseRepository[Reminder]):
    """CRUD напоминаний с поддержкой soft delete."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Reminder)

    async def get_active_for_user(self, user_id: int) -> list[Reminder]:
        """Активные напоминания пользователя (pending, не удалённые)."""
        stmt = (
            select(Reminder)
            .where(
                Reminder.user_id == user_id,
                Reminder.deleted_at.is_(None),
                Reminder.status == REMINDER_STATUS_PENDING,
            )
            .options(selectinload(Reminder.owner))
            .order_by(Reminder.scheduled_at.asc())
            .limit(ACTIVE_REMINDERS_LIMIT)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, reminder_id: int, user_id: int) -> Reminder | None:
        """Soft delete напоминания. Проверяет владельца. Возвращает None при ошибке."""
        reminder = await self.get_by_id(reminder_id)
        if reminder is None or reminder.deleted_at is not None:
            return None
        if reminder.user_id != user_id:
            return None
        reminder.deleted_at = datetime.now(timezone.utc)
        reminder.status = "deleted"
        await self._session.flush()
        return reminder
