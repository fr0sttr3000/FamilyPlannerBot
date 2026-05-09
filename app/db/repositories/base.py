"""Базовый репозиторий с общими CRUD-операциями."""
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)

MAX_LIST_LIMIT = 100


class BaseRepository(Generic[ModelT]):
    """Базовый репозиторий. Содержит общие методы get/save/delete."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, entity_id: int) -> ModelT | None:
        """Получить запись по первичному ключу."""
        return await self._session.get(self._model, entity_id)

    async def save(self, entity: ModelT) -> ModelT:
        """Сохранить новую запись в БД."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def get_all(self, **filters: Any) -> list[ModelT]:
        """Получить все записи с фильтрами."""
        stmt = select(self._model).filter_by(**filters)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
