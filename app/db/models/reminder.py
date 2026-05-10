"""ORM-модель напоминания."""
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

REMINDER_STATUS_PENDING = "pending"
REMINDER_STATUS_FIRED = "fired"
REMINDER_STATUS_DELETED = "deleted"
REMINDER_STATUS_SKIPPED = "skipped"  # US-32: задача уже выполнена, напоминание пропущено


class Reminder(Base):
    """Напоминание пользователя."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=REMINDER_STATUS_PENDING
    )
    fired_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    # Новое поле Sprint 3 (US-32): ссылка на задачу
    task_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,  # ix_reminders_task_id
        comment="Задача, к которой привязано напоминание. NULL = обычное напоминание (US-32).",
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="reminders")  # noqa: F821
    task: Mapped["Task | None"] = relationship(  # noqa: F821
        "Task", foreign_keys=[task_id], back_populates="reminders"
    )

    __table_args__ = (
        Index("idx_reminders_history", "user_id", "created_at"),
        Index("idx_reminders_scheduled", "scheduled_at"),
    )
