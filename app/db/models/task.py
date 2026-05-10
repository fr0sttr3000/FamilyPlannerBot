"""ORM-модель задачи семьи."""
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

# Константы статуса назначения задачи (US-33)
ASSIGNMENT_STATUS_NONE = "none"
ASSIGNMENT_STATUS_PENDING = "pending"
ASSIGNMENT_STATUS_ACCEPTED = "accepted"
ASSIGNMENT_STATUS_DECLINED = "declined"


class Task(Base):
    """Задача в общем семейном списке."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    completed_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    # Новые поля Sprint 3 (US-33)
    assigned_to: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,  # ix_tasks_assigned_to
        comment="Telegram user_id исполнителя (US-33)",
    )
    assignment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="none",
        default=ASSIGNMENT_STATUS_NONE,
        comment="Статус назначения: none/pending/accepted/declined (US-33)",
    )

    # Relationships
    creator: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[user_id], back_populates="tasks"
    )
    completer: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[completed_by], back_populates="completed_tasks"
    )
    assignee: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[assigned_to], back_populates="assigned_tasks"
    )
    reminders: Mapped[list["Reminder"]] = relationship(  # noqa: F821
        "Reminder", foreign_keys="[Reminder.task_id]", back_populates="task"
    )

    __table_args__ = (
        # Частичные индексы определяются в миграции Alembic (0001_initial.py)
        Index("idx_tasks_history", "user_id", "created_at"),
    )
