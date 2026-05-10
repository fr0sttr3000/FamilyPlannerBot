"""Репозиторий задач."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.task import ASSIGNMENT_STATUS_NONE, Task
from app.db.repositories.base import BaseRepository

ACTIVE_TASKS_LIMIT = 100
COMPLETED_TASKS_LIMIT = 20
COMPLETED_TASKS_DAYS = 30


class TaskRepository(BaseRepository[Task]):
    """CRUD задач с поддержкой soft delete."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)

    async def get_active(self) -> list[Task]:
        """Список активных задач (не удалённых и не выполненных), сортировка DESC."""
        stmt = (
            select(Task)
            .where(Task.deleted_at.is_(None), Task.completed_at.is_(None))
            .options(selectinload(Task.creator), selectinload(Task.assignee))
            .order_by(Task.created_at.desc())
            .limit(ACTIVE_TASKS_LIMIT)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_active(self, task_id: int) -> Task | None:
        """Получить активную задачу (deleted_at IS NULL, completed_at IS NULL)."""
        task = await self.get_by_id(task_id)
        if task is None or task.deleted_at is not None or task.completed_at is not None:
            return None
        return task

    async def get_completed(
        self,
        user_id_filter: int | None = None,
        days: int = COMPLETED_TASKS_DAYS,
        limit: int = COMPLETED_TASKS_LIMIT,
    ) -> list[Task]:
        """Список выполненных задач за последние N дней, сортировка DESC.

        Args:
            user_id_filter: фильтрация по пользователю (None = все пользователи).
            days: глубина истории в днях.
            limit: максимальное количество записей.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(Task)
            .where(
                Task.completed_at.is_not(None),
                Task.deleted_at.is_(None),
                Task.completed_at >= cutoff,
            )
            .options(selectinload(Task.completer))
            .order_by(Task.completed_at.desc())
            .limit(limit)
        )
        if user_id_filter is not None:
            stmt = stmt.where(Task.user_id == user_id_filter)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_assignment(
        self,
        task_id: int,
        assignment_status: str,
        assigned_to: int | None = ...,  # type: ignore[assignment]
    ) -> Task | None:
        """Обновить поля назначения задачи.

        Args:
            task_id: ID задачи.
            assignment_status: новый статус назначения.
            assigned_to: новый исполнитель; если не передан (Ellipsis) — не меняется.

        Returns:
            Обновлённую задачу или None если задача не найдена.
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return None
        task.assignment_status = assignment_status
        if assigned_to is not ...:
            task.assigned_to = assigned_to
        await self._session.flush()
        return task

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
