"""Репозиторий заметок."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.note import Note
from app.db.repositories.base import BaseRepository

ACTIVE_NOTES_LIMIT = 50


class NoteRepository(BaseRepository[Note]):
    """CRUD заметок с поддержкой soft delete."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Note)

    async def get_active(self) -> list[Note]:
        """Список активных заметок (не удалённых), сортировка DESC, лимит 50."""
        stmt = (
            select(Note)
            .where(Note.deleted_at.is_(None))
            .options(selectinload(Note.author))
            .order_by(Note.created_at.desc())
            .limit(ACTIVE_NOTES_LIMIT)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def soft_delete(self, note_id: int) -> Note | None:
        """Soft delete заметки. Возвращает None если заметка не найдена."""
        note = await self.get_by_id(note_id)
        if note is None or note.deleted_at is not None:
            return None
        note.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
        return note
