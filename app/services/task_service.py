"""Сервис задач. Бизнес-логика без зависимости от Telegram."""
import logging
from dataclasses import dataclass, field
from datetime import datetime

import pytz

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models.reminder import Reminder
from app.db.models.task import (
    ASSIGNMENT_STATUS_ACCEPTED,
    ASSIGNMENT_STATUS_DECLINED,
    ASSIGNMENT_STATUS_NONE,
    ASSIGNMENT_STATUS_PENDING,
    Task,
)
from app.db.repositories.reminder_repo import ReminderRepository
from app.db.repositories.task_repo import (
    COMPLETED_TASKS_DAYS,
    COMPLETED_TASKS_LIMIT,
    TaskRepository,
)
from app.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

MAX_TASK_TEXT_LENGTH = 500

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


@dataclass
class TaskResult:
    """Результат операции с задачей."""

    success: bool
    task: Task | None = None
    error: str | None = None
    target_user_id: int | None = None


class TaskService:
    """Управление задачами семьи."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = TaskRepository(session)
        self._session = session

    def _parse_scheduled_at(self, date_str: str, time_str: str) -> datetime | None:
        """Парсит дату и время в timezone-aware datetime. Возвращает None при ошибке."""
        try:
            tz = pytz.timezone(settings.timezone)
            naive = datetime.strptime(f"{date_str} {time_str}", f"{DATE_FORMAT} {TIME_FORMAT}")
            return tz.localize(naive)
        except (ValueError, pytz.exceptions.UnknownTimeZoneError):
            return None

    async def create_task(self, user_id: int, text: str) -> TaskResult:
        """Создать новую задачу. Валидирует текст."""
        text = text.strip()
        if not text:
            return TaskResult(success=False, error="Текст задачи не может быть пустым.")
        if len(text) > MAX_TASK_TEXT_LENGTH:
            return TaskResult(
                success=False,
                error=f"Текст задачи слишком длинный (максимум {MAX_TASK_TEXT_LENGTH} символов).",
            )
        task = Task(user_id=user_id, text=text)
        saved = await self._repo.save(task)
        await self._session.commit()
        logger.info("user=%d action=task_create task_id=%d", user_id, saved.id)
        return TaskResult(success=True, task=saved)

    async def get_active_tasks(self) -> list[Task]:
        """Список активных задач семьи."""
        return await self._repo.get_active()

    async def complete_task(self, task_id: int, user_id: int) -> TaskResult:
        """Отметить задачу выполненной."""
        task = await self._repo.mark_done(task_id, user_id)
        if task is None:
            return TaskResult(success=False, error=f"Задача с ID {task_id} не найдена.")
        await self._session.commit()
        logger.info("user=%d action=task_done task_id=%d", user_id, task_id)
        return TaskResult(success=True, task=task)

    async def delete_task(self, task_id: int, user_id: int) -> TaskResult:
        """Soft delete задачи."""
        task = await self._repo.soft_delete(task_id)
        if task is None:
            return TaskResult(success=False, error=f"Задача с ID {task_id} не найдена.")
        await self._session.commit()
        logger.info("user=%d action=task_delete task_id=%d", user_id, task_id)
        return TaskResult(success=True, task=task)

    async def get_completed_tasks(
        self,
        days: int = COMPLETED_TASKS_DAYS,
        limit: int = COMPLETED_TASKS_LIMIT,
    ) -> list[Task]:
        """История выполненных задач за последние N дней (US-13).

        Args:
            days: глубина истории в днях (по умолчанию 30).
            limit: максимальное количество записей (по умолчанию 20).

        Returns:
            Список задач, отсортированных по дате выполнения DESC.
        """
        return await self._repo.get_completed(days=days, limit=limit)

    async def create_task_reminder(
        self, task_id: int, user_id: int, date_str: str, time_str: str
    ) -> TaskResult:
        """Создать напоминание, привязанное к задаче (US-32).

        Проверяет, что задача существует и активна. Парсит дату/время.
        Создаёт запись в reminders с task_id.

        Args:
            task_id: ID задачи.
            user_id: Telegram ID пользователя.
            date_str: дата в формате YYYY-MM-DD.
            time_str: время в формате HH:MM.

        Returns:
            TaskResult(success=True) при успехе,
            TaskResult(success=False, error=...) при ошибке.
        """
        # 1. Проверить что задача существует и активна
        task = await self._repo.get_by_id_active(task_id)
        if task is None:
            return TaskResult(
                success=False,
                error=f"Задача #{task_id} не найдена или уже выполнена.",
            )

        # 2. Распарсить дату/время
        scheduled_at = self._parse_scheduled_at(date_str, time_str)
        if scheduled_at is None:
            return TaskResult(
                success=False,
                error=(
                    "Неверный формат даты или времени.\n"
                    "Пример: /taskremind 3 2026-06-01 10:00"
                ),
            )

        # 3. Создать напоминание с task_id
        reminder_repo = ReminderRepository(self._session)
        reminder = Reminder(
            user_id=user_id,
            text=task.text,
            scheduled_at=scheduled_at,
            task_id=task_id,
        )
        saved = await reminder_repo.save(reminder)
        await self._session.commit()
        logger.info(
            "user=%d action=task_reminder_create task_id=%d reminder_id=%d",
            user_id, task_id, saved.id,
        )
        return TaskResult(success=True, task=task)

    async def assign_task(
        self, task_id: int, assigner_user_id: int, target_username: str
    ) -> TaskResult:
        """Назначить задачу другому пользователю (US-33).

        Проверяет задачу, находит адресата по @username, проверяет статус.
        Устанавливает assignment_status='pending'.

        Args:
            task_id: ID задачи.
            assigner_user_id: Telegram ID назначающего.
            target_username: @username адресата (с @ или без).

        Returns:
            TaskResult(success=True, target_user_id=...) при успехе,
            TaskResult(success=False, error=...) при ошибке.
        """
        # 1. Проверить задачу
        task = await self._repo.get_by_id_active(task_id)
        if task is None:
            return TaskResult(
                success=False,
                error=f"Задача #{task_id} не найдена или уже выполнена.",
            )

        # 2. Проверить что не назначена другому в статусе pending
        if task.assignment_status == ASSIGNMENT_STATUS_PENDING:
            return TaskResult(
                success=False,
                error=f"Задача #{task_id} уже ожидает подтверждения от другого пользователя.",
            )

        # 3. Найти адресата по username
        user_repo = UserRepository(self._session)
        target_user = await user_repo.get_by_username(target_username)
        if target_user is None:
            clean = target_username.lstrip("@")
            return TaskResult(
                success=False,
                error=(
                    f"Пользователь @{clean} не найден в боте.\n"
                    "Попроси его написать боту /start — после этого назначение станет возможным."
                ),
            )

        # 4. Нельзя назначить самому себе
        if target_user.id == assigner_user_id:
            return TaskResult(
                success=False,
                error="Нельзя назначить задачу самому себе.",
            )

        # 5. UPDATE assignment
        await self._repo.update_assignment(
            task_id=task_id,
            assigned_to=target_user.id,
            assignment_status=ASSIGNMENT_STATUS_PENDING,
        )
        await self._session.commit()
        logger.info(
            "user=%d action=task_assign task_id=%d assignee=%d",
            assigner_user_id, task_id, target_user.id,
        )
        return TaskResult(success=True, task=task, target_user_id=target_user.id)

    async def accept_assignment(self, task_id: int) -> None:
        """Принять назначение задачи (статус → accepted).

        Args:
            task_id: ID задачи.
        """
        await self._repo.update_assignment(
            task_id=task_id,
            assignment_status=ASSIGNMENT_STATUS_ACCEPTED,
        )
        await self._session.commit()
        logger.info("action=task_accept task_id=%d", task_id)

    async def decline_assignment(self, task_id: int) -> None:
        """Отклонить назначение задачи (статус → declined, assigned_to → NULL).

        Args:
            task_id: ID задачи.
        """
        await self._repo.update_assignment(
            task_id=task_id,
            assigned_to=None,
            assignment_status=ASSIGNMENT_STATUS_DECLINED,
        )
        await self._session.commit()
        logger.info("action=task_decline task_id=%d", task_id)

    async def get_task_by_id(self, task_id: int) -> Task | None:
        """Получить задачу по ID (без фильтра deleted_at — для callback-проверки).

        Args:
            task_id: ID задачи.

        Returns:
            Task или None.
        """
        return await self._repo.get_by_id(task_id)

    async def get_active_task_by_id(self, task_id: int) -> Task | None:
        """Получить активную задачу (deleted_at IS NULL, completed_at IS NULL).

        Args:
            task_id: ID задачи.

        Returns:
            Task или None если не активна или не существует.
        """
        return await self._repo.get_by_id_active(task_id)
