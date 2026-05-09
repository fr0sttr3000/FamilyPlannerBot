"""Репозиторий событий календаря."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.event import Event
from app.db.repositories.base import BaseRepository

UPCOMING_EVENTS_LIMIT = 30


class EventRepository(BaseRepository[Event]):
    """CRUD событий календаря."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Event)

    async def get_upcoming(self, from_date: date) -> list[Event]:
        """Предстоящие события начиная с указанной даты, лимит 30."""
        stmt = (
            select(Event)
            .where(
                Event.deleted_at.is_(None),
                Event.event_date >= from_date,
            )
            .options(selectinload(Event.creator))
            .order_by(Event.event_date.asc())
            .limit(UPCOMING_EVENTS_LIMIT)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
