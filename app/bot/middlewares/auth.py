"""AuthMiddleware — фильтрация неавторизованных пользователей.

Реализует гибридный whitelist (ADR-04):
- Источник авторизации: ALLOWED_USERS в .env (O(1) проверка в памяти)
- Аудит: UPSERT в таблицу users при каждом авторизованном запросе
- Неавторизованные: молча игнорируются (NFR-SEC-03, BR-04)
"""
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    """Проверяет Telegram ID против ALLOWED_USERS и выполняет UPSERT аудита."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """Проверить авторизацию перед передачей управления handler-у."""
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        if user.id not in settings.allowed_users:
            logger.warning(
                "Попытка неавторизованного доступа telegram_id=%d", user.id
            )
            return None

        # Аудит активности авторизованного пользователя
        session: AsyncSession | None = data.get("session")
        if session is not None:
            try:
                repo = UserRepository(session)
                await repo.upsert(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name or "Пользователь",
                )
            except Exception:
                logger.exception("Ошибка при UPSERT пользователя user_id=%d", user.id)

        return await handler(event, data)
