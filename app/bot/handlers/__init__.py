"""Handlers для Telegram-команд."""
from app.bot.handlers import calendar, notes, reminders, start, tasks

__all__ = ["start", "tasks", "notes", "reminders", "calendar"]
