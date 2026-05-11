"""Привести все TIMESTAMP-колонки к TIMESTAMP WITH TIME ZONE.

Revision ID: 0003_timestamp_timezone
Revises: 0002_sprint3_assignment
Create Date: 2026-05-11

Причина: asyncpg возвращает datetime без tzinfo для TIMESTAMP (без TZ),
что вызывает ошибки сравнения timezone-aware vs naive datetime в scheduler.
Фикс переводит все колонки в TIMESTAMPTZ (PostgreSQL хранит UTC).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import TIMESTAMP

revision: str = "0003_timestamp_timezone"
down_revision: Union[str, None] = "0002_sprint3_assignment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TZ = TIMESTAMP(timezone=True)


def upgrade() -> None:
    """Перевести все datetime-колонки на TIMESTAMPTZ."""

    # users
    op.alter_column("users", "last_active_at", type_=_TZ, existing_nullable=False)
    op.alter_column("users", "created_at", type_=_TZ, existing_nullable=False)

    # tasks
    op.alter_column("tasks", "completed_at", type_=_TZ, existing_nullable=True)
    op.alter_column("tasks", "deleted_at", type_=_TZ, existing_nullable=True)
    op.alter_column("tasks", "created_at", type_=_TZ, existing_nullable=False)

    # reminders
    op.alter_column("reminders", "scheduled_at", type_=_TZ, existing_nullable=False)
    op.alter_column("reminders", "fired_at", type_=_TZ, existing_nullable=True)
    op.alter_column("reminders", "deleted_at", type_=_TZ, existing_nullable=True)
    op.alter_column("reminders", "created_at", type_=_TZ, existing_nullable=False)

    # notes
    op.alter_column("notes", "deleted_at", type_=_TZ, existing_nullable=True)
    op.alter_column("notes", "created_at", type_=_TZ, existing_nullable=False)

    # events
    op.alter_column("events", "deleted_at", type_=_TZ, existing_nullable=True)
    op.alter_column("events", "created_at", type_=_TZ, existing_nullable=False)


def downgrade() -> None:
    """Откатить TIMESTAMPTZ → TIMESTAMP (без TZ)."""
    _NO_TZ = sa.TIMESTAMP()

    # events
    op.alter_column("events", "created_at", type_=_NO_TZ, existing_nullable=False)
    op.alter_column("events", "deleted_at", type_=_NO_TZ, existing_nullable=True)

    # notes
    op.alter_column("notes", "created_at", type_=_NO_TZ, existing_nullable=False)
    op.alter_column("notes", "deleted_at", type_=_NO_TZ, existing_nullable=True)

    # reminders
    op.alter_column("reminders", "created_at", type_=_NO_TZ, existing_nullable=False)
    op.alter_column("reminders", "deleted_at", type_=_NO_TZ, existing_nullable=True)
    op.alter_column("reminders", "fired_at", type_=_NO_TZ, existing_nullable=True)
    op.alter_column("reminders", "scheduled_at", type_=_NO_TZ, existing_nullable=False)

    # tasks
    op.alter_column("tasks", "created_at", type_=_NO_TZ, existing_nullable=False)
    op.alter_column("tasks", "deleted_at", type_=_NO_TZ, existing_nullable=True)
    op.alter_column("tasks", "completed_at", type_=_NO_TZ, existing_nullable=True)

    # users
    op.alter_column("users", "created_at", type_=_NO_TZ, existing_nullable=False)
    op.alter_column("users", "last_active_at", type_=_NO_TZ, existing_nullable=False)
