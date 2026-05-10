"""Unit-тесты для admin handler (/adminoverview, US-23)."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.bot.handlers.admin import adminoverview_handler
from app.services.admin_service import AdminOverview


def make_message(user_id: int) -> MagicMock:
    """Создать мок Message с заданным user_id."""
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = user_id
    message.answer = AsyncMock()
    return message


def make_overview(
    active_tasks_count: int = 3,
    upcoming_reminders: list | None = None,
    week_events: list | None = None,
) -> AdminOverview:
    """Создать мок AdminOverview с тестовыми данными."""
    if upcoming_reminders is None:
        upcoming_reminders = []
    if week_events is None:
        week_events = []
    return AdminOverview(
        generated_at=datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
        active_tasks_count=active_tasks_count,
        upcoming_reminders=upcoming_reminders,
        week_events=week_events,
    )


# ────────────────────────── TC-ADMIN-02: не-владелец ──────────────────────────


async def test_admin_overview_non_owner_rejected():
    """Не-владелец → отказ 'Команда недоступна.', AdminService не создаётся."""
    message = make_message(user_id=987654321)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = 123456789  # другой ID

    with (
        patch("app.bot.handlers.admin.settings", mock_settings),
        patch("app.bot.handlers.admin.AdminService") as MockAdminService,
    ):
        await adminoverview_handler(message, session)

    # Ответ содержит отказ
    message.answer.assert_awaited_once()
    reply_text = message.answer.call_args.args[0]
    assert "недоступна" in reply_text.lower()

    # AdminService вообще не создавался — агрегация не выполнялась
    MockAdminService.assert_not_called()


async def test_admin_overview_non_owner_no_data_leaked():
    """Не-владелец → ответ не содержит данных о задачах/напоминаниях."""
    message = make_message(user_id=111111)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = 999999

    with patch("app.bot.handlers.admin.settings", mock_settings):
        await adminoverview_handler(message, session)

    reply_text = message.answer.call_args.args[0]
    # Ответ не раскрывает системные данные
    assert "задач" not in reply_text.lower()
    assert "напоминани" not in reply_text.lower()
    assert "событи" not in reply_text.lower()


# ────────────────────────── TC-ADMIN-01: владелец получает данные ──────────────────────────


async def test_admin_overview_owner_gets_data():
    """Владелец → AdminService.get_overview() вызван, ответ содержит сводку."""
    owner_id = 123456789
    message = make_message(user_id=owner_id)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = owner_id

    fake_overview = make_overview(active_tasks_count=5)

    with (
        patch("app.bot.handlers.admin.settings", mock_settings),
        patch("app.bot.handlers.admin.AdminService") as MockAdminService,
    ):
        mock_service = MockAdminService.return_value
        mock_service.get_overview = AsyncMock(return_value=fake_overview)

        await adminoverview_handler(message, session)

    # AdminService создан с сессией
    MockAdminService.assert_called_once_with(session)
    # get_overview вызван
    mock_service.get_overview.assert_awaited_once()
    # Ответ отправлен
    message.answer.assert_awaited_once()
    reply_text = message.answer.call_args.args[0]
    # Содержит количество задач
    assert "5" in reply_text


async def test_admin_overview_owner_response_contains_active_tasks():
    """Владелец → ответ содержит блок 'Активных задач'."""
    owner_id = 123456789
    message = make_message(user_id=owner_id)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = owner_id

    fake_overview = make_overview(active_tasks_count=7)

    with (
        patch("app.bot.handlers.admin.settings", mock_settings),
        patch("app.bot.handlers.admin.AdminService") as MockAdminService,
    ):
        mock_service = MockAdminService.return_value
        mock_service.get_overview = AsyncMock(return_value=fake_overview)

        await adminoverview_handler(message, session)

    reply_text = message.answer.call_args.args[0]
    assert "Активных задач" in reply_text
    assert "7" in reply_text


async def test_admin_overview_owner_response_contains_reminders_section():
    """Владелец → ответ содержит блок 'Ближайшие напоминания'."""
    owner_id = 123456789
    message = make_message(user_id=owner_id)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = owner_id

    # Напоминание-мок
    fake_reminder = MagicMock()
    fake_reminder.scheduled_at = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    fake_reminder.text = "Купить молоко"
    fake_reminder.task_id = None

    fake_overview = make_overview(
        active_tasks_count=2,
        upcoming_reminders=[fake_reminder],
    )

    with (
        patch("app.bot.handlers.admin.settings", mock_settings),
        patch("app.bot.handlers.admin.AdminService") as MockAdminService,
    ):
        mock_service = MockAdminService.return_value
        mock_service.get_overview = AsyncMock(return_value=fake_overview)

        await adminoverview_handler(message, session)

    reply_text = message.answer.call_args.args[0]
    assert "Ближайшие напоминания" in reply_text
    assert "Купить молоко" in reply_text


async def test_admin_overview_owner_empty_reminders():
    """Владелец с пустым списком напоминаний → ответ содержит 'Нет предстоящих'."""
    owner_id = 123456789
    message = make_message(user_id=owner_id)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = owner_id

    fake_overview = make_overview(upcoming_reminders=[])

    with (
        patch("app.bot.handlers.admin.settings", mock_settings),
        patch("app.bot.handlers.admin.AdminService") as MockAdminService,
    ):
        mock_service = MockAdminService.return_value
        mock_service.get_overview = AsyncMock(return_value=fake_overview)

        await adminoverview_handler(message, session)

    reply_text = message.answer.call_args.args[0]
    assert "Нет предстоящих" in reply_text


async def test_admin_overview_owner_with_task_reminder():
    """Владелец → напоминание с task_id отображает '(задача #N)' в ответе."""
    owner_id = 123456789
    message = make_message(user_id=owner_id)
    session = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.owner_id = owner_id

    fake_reminder = MagicMock()
    fake_reminder.scheduled_at = datetime(2026, 5, 20, 9, 0, tzinfo=timezone.utc)
    fake_reminder.text = "Проверить задачу"
    fake_reminder.task_id = 42  # привязано к задаче

    fake_overview = make_overview(
        active_tasks_count=1,
        upcoming_reminders=[fake_reminder],
    )

    with (
        patch("app.bot.handlers.admin.settings", mock_settings),
        patch("app.bot.handlers.admin.AdminService") as MockAdminService,
    ):
        mock_service = MockAdminService.return_value
        mock_service.get_overview = AsyncMock(return_value=fake_overview)

        await adminoverview_handler(message, session)

    reply_text = message.answer.call_args.args[0]
    # Должно содержать ссылку на задачу
    assert "задача #42" in reply_text


async def test_admin_overview_no_from_user():
    """from_user is None → handler завершается без ответа."""
    message = MagicMock()
    message.from_user = None
    message.answer = AsyncMock()
    session = AsyncMock()

    await adminoverview_handler(message, session)

    message.answer.assert_not_awaited()
