"""Сервис событий календаря."""
import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.event import Event
from app.db.repositories.event_repo import EventRepository

logger = logging.getLogger(__name__)

DATE_FORMAT = "%Y-%m-%d"
MAX_EVENT_TEXT_LENGTH = 500


@dataclass
class EventResult:
    """Результат операции с событием."""

    success: bool
    event: Event | None = None
    error: str | None = None


class EventService:
    """Управление событиями общего календаря."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = EventRepository(session)
        self._session = session

    def _parse_date(self, date_str: str) -> date | None:
        """Парсит строку даты. Возвращает None при ошибке."""
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            return None

    async def create_event(self, user_id: int, date_str: str, text: str) -> EventResult:
        """Создать событие в календаре. Валидирует дату и текст."""
        text = text.strip()
        if not text:
            return EventResult(success=False, error="Описание события не может быть пустым.")

        event_date = self._parse_date(date_str)
        if event_date is None:
            return EventResult(
                success=False,
                error="Неверный формат даты.\nПример: /addevent 2026-05-10 День рождения",
            )

        if len(text) > MAX_EVENT_TEXT_LENGTH:
            return EventResult(
                success=False,
                error=f"Описание слишком длинное (максимум {MAX_EVENT_TEXT_LENGTH} символов).",
            )

        event = Event(user_id=user_id, event_date=event_date, text=text)
        saved = await self._repo.save(event)
        await self._session.commit()
        logger.info("user=%d action=event_create event_id=%d", user_id, saved.id)
        return EventResult(success=True, event=saved)

    async def get_upcoming_events(self, from_date: date) -> list[Event]:
        """Предстоящие события начиная с указанной даты."""
        return await self._repo.get_upcoming(from_date)
