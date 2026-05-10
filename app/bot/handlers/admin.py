"""Handlers для административных команд.

Команды: /adminoverview
Доступ только владельцу (settings.owner_id).
"""
import logging
from datetime import timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.admin_service import (
    ADMIN_UPCOMING_REMINDERS_LIMIT,
    ADMIN_WEEK_DAYS,
    AdminService,
)

logger = logging.getLogger(__name__)

router = Router(name="admin")


@router.message(Command("adminoverview"))
async def adminoverview_handler(message: Message, session: AsyncSession) -> None:
    """Административная сводка состояния бота (US-23).

    Только для владельца (settings.owner_id).
    Показывает: количество активных задач, ближайшие 5 напоминаний,
    события на текущую неделю.
    """
    if message.from_user is None:
        return

    if message.from_user.id != settings.owner_id:
        await message.answer("Команда недоступна.")
        logger.warning(
            "adminoverview: попытка доступа от незарегистрированного пользователя user=%d",
            message.from_user.id,
        )
        return

    try:
        service = AdminService(session)
        overview = await service.get_overview()

        week_end = overview.generated_at + timedelta(days=ADMIN_WEEK_DAYS)

        # Форматирование ответа
        lines = [
            f"<b>Сводка бота на {overview.generated_at.strftime('%d.%m.%Y %H:%M')} UTC</b>\n"
        ]

        # Задачи
        lines.append(f"📋 <b>Активных задач:</b> {overview.active_tasks_count}")

        # Напоминания
        lines.append(
            f"\n⏰ <b>Ближайшие напоминания ({ADMIN_UPCOMING_REMINDERS_LIMIT}):</b>"
        )
        if overview.upcoming_reminders:
            for r in overview.upcoming_reminders:
                scheduled_str = r.scheduled_at.strftime("%d.%m %H:%M")
                task_info = f" (задача #{r.task_id})" if r.task_id else ""
                lines.append(f"• {scheduled_str} — {r.text[:60]}{task_info}")
        else:
            lines.append("  Нет предстоящих напоминаний.")

        # События на неделю
        lines.append(f"\n📅 <b>События на неделю (до {week_end.strftime('%d.%m')}):</b>")
        if overview.week_events:
            for e in overview.week_events:
                lines.append(f"• {e.event_date.strftime('%d.%m')} — {e.text[:60]}")
        else:
            lines.append("  Событий на неделю нет.")

        await message.answer("\n".join(lines), parse_mode="HTML")
        logger.info("user=%d action=adminoverview", message.from_user.id)

    except Exception:
        logger.exception("Ошибка в /adminoverview user=%d", message.from_user.id)
        await message.answer("Не удалось получить сводку. Попробуйте позже.")
