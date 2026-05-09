"""Сервис задач. Бизнес-логика без зависимости от Telegram."""
import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.db.repositories.task_repo import TaskRepository

logger = logging.getLogger(__name__)

MAX_TASK_TEXT_LENGTH = 500


@dataclass
class TaskResult:
    """Результат операции с задачей."""

    success: bool
    task: Task | None = None
    error: str | None = None


class TaskService:
    """Управление задачами семьи."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = TaskRepository(session)
        self._session = session

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
