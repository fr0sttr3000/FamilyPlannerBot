"""Сервис заметок. Бизнес-логика без зависимости от Telegram."""
import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.note import Note
from app.db.repositories.note_repo import NoteRepository

logger = logging.getLogger(__name__)

MAX_NOTE_TEXT_LENGTH = 2000


@dataclass
class NoteResult:
    """Результат операции с заметкой."""

    success: bool
    note: Note | None = None
    error: str | None = None


class NoteService:
    """Управление заметками."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = NoteRepository(session)
        self._session = session

    async def create_note(self, user_id: int, text: str) -> NoteResult:
        """Создать новую заметку. Валидирует текст."""
        text = text.strip()
        if not text:
            return NoteResult(success=False, error="Текст заметки не может быть пустым.")
        if len(text) > MAX_NOTE_TEXT_LENGTH:
            return NoteResult(
                success=False,
                error=f"Заметка слишком длинная (максимум {MAX_NOTE_TEXT_LENGTH} символов).",
            )
        note = Note(user_id=user_id, text=text)
        saved = await self._repo.save(note)
        await self._session.commit()
        logger.info("user=%d action=note_create note_id=%d", user_id, saved.id)
        return NoteResult(success=True, note=saved)

    async def get_active_notes(self) -> list[Note]:
        """Список активных заметок."""
        return await self._repo.get_active()
