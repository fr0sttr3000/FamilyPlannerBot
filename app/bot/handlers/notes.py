"""Handlers для управления заметками.

Команды: /notes, /addnote
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.note_service import NoteService

logger = logging.getLogger(__name__)

router = Router(name="notes")

NOTES_EMPTY = "Заметок нет. Добавьте первую: /addnote Текст заметки"
ADDNOTE_USAGE = "Укажите текст заметки. Пример: /addnote Рецепт борща: ..."

NOTE_PREVIEW_LENGTH = 100


def _format_notes_list(notes: list) -> str:
    """Форматирует список заметок (превью 100 символов, US-15)."""
    lines = ["📝 *Заметки:*\n"]
    for note in notes:
        author = note.author.first_name if note.author else "Неизвестно"
        date_str = note.created_at.strftime("%d.%m")
        preview = note.text[:NOTE_PREVIEW_LENGTH]
        if len(note.text) > NOTE_PREVIEW_LENGTH:
            preview += "…"
        lines.append(f"• [{note.id}] {preview} _{author}, {date_str}_")
    return "\n".join(lines)


@router.message(Command("notes"))
async def notes_handler(message: Message, session: AsyncSession) -> None:
    """Показать список активных заметок (лимит 50, US-15)."""
    if message.from_user is None:
        return
    try:
        service = NoteService(session)
        notes = await service.get_active_notes()
        if not notes:
            await message.answer(NOTES_EMPTY)
            return
        await message.answer(_format_notes_list(notes), parse_mode="Markdown")
        logger.info("user=%d action=notes_list count=%d", message.from_user.id, len(notes))
    except Exception:
        logger.exception("Ошибка в /notes user=%d", message.from_user.id)
        await message.answer("Не удалось загрузить заметки. Попробуйте позже.")


@router.message(Command("addnote"))
async def addnote_handler(message: Message, session: AsyncSession) -> None:
    """Добавить новую заметку."""
    if message.from_user is None:
        return
    text = (message.text or "").removeprefix("/addnote").strip()
    if not text:
        await message.answer(ADDNOTE_USAGE)
        return
    try:
        service = NoteService(session)
        result = await service.create_note(message.from_user.id, text)
        if result.success and result.note:
            await message.answer(f"✅ Заметка добавлена (ID: {result.note.id})")
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /addnote user=%d", message.from_user.id)
        await message.answer("Не удалось добавить заметку. Попробуйте позже.")
