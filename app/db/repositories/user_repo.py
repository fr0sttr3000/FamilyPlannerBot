"""Репозиторий пользователей."""
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """CRUD и аудит пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def upsert(self, telegram_id: int, username: str | None, first_name: str) -> User:
        """UPSERT пользователя: создать или обновить last_active_at."""
        now = datetime.now(timezone.utc)
        stmt = (
            pg_insert(User)
            .values(
                id=telegram_id,
                username=username,
                first_name=first_name,
                last_active_at=now,
                created_at=now,
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "username": username,
                    "first_name": first_name,
                    "last_active_at": now,
                },
            )
            .returning(User)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()
