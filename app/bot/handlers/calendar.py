"""Handlers для управления событиями календаря.

Команды: /calendar, /addevent
"""
import logging
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_service import EventService

logger = logging.getLogger(__name__)

router = Router(name="calendar")

CALENDAR_EMPTY = (
    "Предстоящих событий нет.\n"
    "Пример: /addevent 2026-05-15 День рождения Маши"
)
ADDEVENT_USAGE = (
    "Формат: /addevent ГГГГ-ММ-ДД Описание события\n"
    "Пример: /addevent 2026-05-15 День рождения Маши"
)


def _format_events_list(events: list) -> str:
    """Форматирует список предстоящих событий."""
    lines = ["📅 *Предстоящие события:*\n"]
    current_month = None
    for event in events:
        month = event.event_date.strftime("%B %Y")
        if month != current_month:
            lines.append(f"\n*{month}*")
            current_month = month
        day = event.event_date.strftime("%d.%m")
        creator = event.creator.first_name if event.creator else "?"
        lines.append(f"• {day} — {event.text} _{creator}_")
    return "\n".join(lines)


@router.message(Command("calendar"))
async def calendar_handler(message: Message, session: AsyncSession) -> None:
    """Показать предстоящие события общего календаря."""
    if message.from_user is None:
        return
    try:
        service = EventService(session)
        events = await service.get_upcoming_events(date.today())
        if not events:
            await message.answer(CALENDAR_EMPTY)
            return
        await message.answer(_format_events_list(events), parse_mode="Markdown")
        logger.info("user=%d action=calendar_view count=%d", message.from_user.id, len(events))
    except Exception:
        logger.exception("Ошибка в /calendar user=%d", message.from_user.id)
        await message.answer("Не удалось загрузить календарь. Попробуйте позже.")


@router.message(Command("addevent"))
async def addevent_handler(message: Message, session: AsyncSession) -> None:
    """Добавить событие в общий календарь."""
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/addevent").strip()
    parts = args.split(maxsplit=1)
    if len(parts) < 2:  # noqa: PLR2004
        await message.answer(ADDEVENT_USAGE)
        return
    date_str, text = parts[0], parts[1]
    try:
        service = EventService(session)
        result = await service.create_event(message.from_user.id, date_str, text)
        if result.success and result.event:
            event_date = result.event.event_date.strftime("%d.%m.%Y")
            await message.answer(
                f"✅ Событие добавлено: {event_date} — {result.event.text} "
                f"(ID: {result.event.id})"
            )
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /addevent user=%d", message.from_user.id)
        await message.answer("Не удалось добавить событие. Попробуйте позже.")
