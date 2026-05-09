"""Репозиторий задач."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.task import Task
from app.db.repositories.base import BaseRepository

ACTIVE_TASKS_LIMIT = 100


class TaskRepository(BaseRepository[Task]):
    """CRUD задач с поддержкой soft delete."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)

    async def get_active(self) -> list[Task]:
        """Список активных задач (не удалённых и не выполненных), сортировка DESC."""
        stmt = (
            select(Task)
            .where(Task.deleted_at.is_(None), Task.completed_at.is_(None))
            .options(selectinload(Task.creator))
            .order_by(Task.created_at.desc())
            .limit(ACTIVE_TASKS_LIMIT)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def mark_done(self, task_id: int, user_id: int) -> Task | None:
        """Отметить задачу выполненной. Возвращает None если задача не найдена."""
        task = await self.get_by_id(task_id)
        if task is None or task.deleted_at is not None:
            return None
        task.completed_by = user_id
        task.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return task

    async def soft_delete(self, task_id: int) -> Task | None:
        """Soft delete задачи. Возвращает None если задача не найдена."""
        task = await self.get_by_id(task_id)
        if task is None or task.deleted_at is not None:
            return None
        task.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        return task
