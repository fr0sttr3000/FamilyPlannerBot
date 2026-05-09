"""DBSessionMiddleware — инъекция async-сессии в handlers.

Создаёт AsyncSession для каждого Update и передаёт через data['session'].
"""
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class DBSessionMiddleware(BaseMiddleware):
    """Передаёт AsyncSession в data['session'] для каждого Update."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Создать сессию, передать в data, закрыть после обработки."""
        async with self._session_factory() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise
