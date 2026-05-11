"""ORM-модель пользователя.

Таблица users хранит аудит активности авторизованных участников.
Источник авторизации — ALLOWED_USERS в .env (ADR-04).
"""
from datetime import datetime

from sqlalchemy import BigInteger, String, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class User(Base):
    """Пользователь бота (аудит активности)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="Telegram User ID")
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", foreign_keys="Task.user_id", back_populates="creator"
    )
    completed_tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", foreign_keys="Task.completed_by", back_populates="completer"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", foreign_keys="Task.assigned_to", back_populates="assignee"
    )
    notes: Mapped[list["Note"]] = relationship("Note", back_populates="author")  # noqa: F821
    reminders: Mapped[list["Reminder"]] = relationship("Reminder", back_populates="owner")  # noqa: F821
    events: Mapped[list["Event"]] = relationship("Event", back_populates="creator")  # noqa: F821
