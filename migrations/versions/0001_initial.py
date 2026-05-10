"""Начальная миграция: создание всех таблиц.

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-09

Создаёт таблицы: users, tasks, notes, reminders, events
со всеми индексами из HLD раздел 6.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создать все таблицы и индексы."""

    # --- Таблица users ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="Telegram User ID"),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column(
            "last_active_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- Таблица tasks ---
    op.create_table(
        "tasks",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("completed_by", sa.BigInteger(), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Частичный индекс для активных задач
    op.create_index(
        "idx_tasks_active",
        "tasks",
        ["created_at"],
        postgresql_where=sa.text("deleted_at IS NULL AND completed_at IS NULL"),
    )
    op.create_index("idx_tasks_history", "tasks", ["user_id", "created_at"])

    # --- Таблица notes ---
    op.create_table(
        "notes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_notes_active",
        "notes",
        ["created_at"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_notes_history", "notes", ["user_id", "created_at"])

    # --- Таблица reminders ---
    op.create_table(
        "reminders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("fired_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_reminders_user_status",
        "reminders",
        ["user_id", "status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_reminders_scheduled_pending",
        "reminders",
        ["scheduled_at"],
        postgresql_where=sa.text("status = 'pending'"),
    )
    op.create_index("idx_reminders_history", "reminders", ["user_id", "created_at"])
    op.create_index("idx_reminders_scheduled", "reminders", ["scheduled_at"])

    # --- Таблица events ---
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_events_date",
        "events",
        ["event_date"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_month",
        "events",
        [sa.text("date_trunc('month', event_date::timestamp)")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("idx_events_creator", "events", ["user_id", "event_date"])


def downgrade() -> None:
    """Удалить все таблицы и индексы."""
    op.drop_table("events")
    op.drop_table("reminders")
    op.drop_table("notes")
    op.drop_table("tasks")
    op.drop_table("users")
