"""ORM-модель заметки."""
from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base


class Note(Base):
    """Заметка члена семьи."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())

    # Relationship
    author: Mapped["User"] = relationship("User", back_populates="notes")  # noqa: F821

    __table_args__ = (
        Index("idx_notes_history", "user_id", "created_at"),
    )
