"""ORM-модель события календаря."""
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Text, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Event(Base):
    """Событие в общем семейном календаре."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationship
    creator: Mapped["User"] = relationship("User", back_populates="events")  # noqa: F821

    __table_args__ = (
        Index("idx_events_date", "event_date"),
        Index("idx_events_creator", "user_id", "event_date"),
    )
