"""Репозитории для доступа к данным."""
from app.db.repositories.event_repo import EventRepository
from app.db.repositories.note_repo import NoteRepository
from app.db.repositories.reminder_repo import ReminderRepository
from app.db.repositories.task_repo import TaskRepository
from app.db.repositories.user_repo import UserRepository

__all__ = [
    "UserRepository",
    "TaskRepository",
    "NoteRepository",
    "ReminderRepository",
    "EventRepository",
]
