"""Handlers для управления напоминаниями.

Sprint 1: создание и просмотр записей в БД (без APScheduler-доставки).
Доставка напоминаний добавляется в Sprint 2.

Команды: /reminders, /addreminder, /delreminder
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

router = Router(name="reminders")

REMINDERS_EMPTY = (
    "Активных напоминаний нет.\n"
    "Пример: /addreminder 2026-05-10 14:30 Купить молоко"
)
ADDREMINDER_USAGE = (
    "Формат: /addreminder ГГГГ-ММ-ДД ЧЧ:ММ Текст\n"
    "Пример: /addreminder 2026-05-10 14:30 Позвонить врачу"
)
DELREMINDER_USAGE = "Укажите ID напоминания. Пример: /delreminder 3"


def _format_reminders_list(reminders: list) -> str:
    """Форматирует список напоминаний."""
    lines = ["⏰ *Мои напоминания:*\n"]
    for rem in reminders:
        scheduled = rem.scheduled_at.strftime("%d.%m.%Y %H:%M")
        lines.append(f"• [{rem.id}] {scheduled} — {rem.text}")
    lines.append("\n_⚠️ Доставка напоминаний включается в Sprint 2_")
    return "\n".join(lines)


@router.message(Command("reminders"))
async def reminders_handler(message: Message, session: AsyncSession) -> None:
    """Показать список активных напоминаний пользователя."""
    if message.from_user is None:
        return
    try:
        service = ReminderService(session)
        reminders = await service.get_active_reminders(message.from_user.id)
        if not reminders:
            await message.answer(REMINDERS_EMPTY)
            return
        await message.answer(_format_reminders_list(reminders), parse_mode="Markdown")
        logger.info(
            "user=%d action=reminders_list count=%d",
            message.from_user.id,
            len(reminders),
        )
    except Exception:
        logger.exception("Ошибка в /reminders user=%d", message.from_user.id)
        await message.answer("Не удалось загрузить напоминания. Попробуйте позже.")


@router.message(Command("addreminder"))
async def addreminder_handler(message: Message, session: AsyncSession) -> None:
    """Создать напоминание (сохранить в БД, доставка — Sprint 2)."""
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/addreminder").strip()
    parts = args.split(maxsplit=2)
    if len(parts) < 3:  # noqa: PLR2004
        await message.answer(ADDREMINDER_USAGE)
        return
    date_str, time_str, text = parts[0], parts[1], parts[2]
    try:
        service = ReminderService(session)
        result = await service.create_reminder(
            message.from_user.id, date_str, time_str, text
        )
        if result.success and result.reminder:
            scheduled = result.reminder.scheduled_at.strftime("%d.%m.%Y %H:%M")
            await message.answer(
                f"✅ Напоминание создано: {scheduled} — {result.reminder.text} "
                f"(ID: {result.reminder.id})\n"
                f"_⚠️ Доставка включается в Sprint 2_",
                parse_mode="Markdown",
            )
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /addreminder user=%d", message.from_user.id)
        await message.answer("Не удалось создать напоминание. Попробуйте позже.")


@router.message(Command("delreminder"))
async def delreminder_handler(message: Message, session: AsyncSession) -> None:
    """Удалить напоминание (soft delete)."""
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/delreminder").strip()
    if not args.isdigit():
        await message.answer(DELREMINDER_USAGE)
        return
    try:
        service = ReminderService(session)
        result = await service.delete_reminder(int(args), message.from_user.id)
        if result.success:
            await message.answer(f"🗑 Напоминание {args} удалено.")
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /delreminder user=%d", message.from_user.id)
        await message.answer("Не удалось удалить напоминание. Попробуйте позже.")
