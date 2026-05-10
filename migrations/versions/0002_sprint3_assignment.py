"""Sprint 3: добавить task_id в reminders, assigned_to и assignment_status в tasks.

Revision ID: 0002_sprint3_assignment
Revises: 0001_initial
Create Date: 2026-05-10

US-32: reminders.task_id — ссылка на задачу (NULL = обычное напоминание)
US-33: tasks.assigned_to  — кому назначена задача
       tasks.assignment_status — none/pending/accepted/declined
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_sprint3_assignment"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавить поля для US-32 (task_id) и US-33 (assigned_to, assignment_status)."""

    # --- reminders: task_id (US-32) ---
    op.add_column(
        "reminders",
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
            comment="Задача, к которой привязано напоминание (US-32). NULL = обычное напоминание.",
        ),
    )
    op.create_index("ix_reminders_task_id", "reminders", ["task_id"])

    # --- tasks: assigned_to (US-33) ---
    op.add_column(
        "tasks",
        sa.Column(
            "assigned_to",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="Telegram user_id исполнителя, которому назначена задача (US-33).",
        ),
    )
    op.create_index("ix_tasks_assigned_to", "tasks", ["assigned_to"])

    # --- tasks: assignment_status (US-33) ---
    op.add_column(
        "tasks",
        sa.Column(
            "assignment_status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'none'"),
            comment="Статус назначения: none/pending/accepted/declined (US-33).",
        ),
    )


def downgrade() -> None:
    """Откатить добавленные поля Sprint 3."""

    # tasks: убрать в обратном порядке
    op.drop_column("tasks", "assignment_status")
    op.drop_index("ix_tasks_assigned_to", table_name="tasks")
    op.drop_column("tasks", "assigned_to")

    # reminders
    op.drop_index("ix_reminders_task_id", table_name="reminders")
    op.drop_column("reminders", "task_id")
