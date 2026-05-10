"""Unit-тесты для ReminderService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.reminder_service import ReminderService


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def fake_reminder():
    reminder = MagicMock()
    reminder.id = 1
    return reminder


async def test_create_reminder_empty_text(session):
    """create_reminder с пустым текстом → success=False, 'пустым' в error."""
    with patch("app.services.reminder_service.ReminderRepository"):
        service = ReminderService(session)
        result = await service.create_reminder(1, "2026-06-01", "10:00", "  ")
    assert result.success is False
    assert "пустым" in result.error


async def test_create_reminder_invalid_date(session):
    """create_reminder с невалидной датой/временем → success=False."""
    with patch("app.services.reminder_service.ReminderRepository"):
        service = ReminderService(session)
        result = await service.create_reminder(1, "invalid", "99:99", "Test")
    assert result.success is False


async def test_create_reminder_success(session, fake_reminder):
    """create_reminder с валидными данными → success=True, reminder — мок."""
    with patch("app.services.reminder_service.ReminderRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.save = AsyncMock(return_value=fake_reminder)
        service = ReminderService(session)
        result = await service.create_reminder(1, "2026-06-01", "10:00", "Doctor")
    assert result.success is True
    assert result.reminder is fake_reminder


async def test_delete_reminder_not_found(session):
    """delete_reminder при soft_delete → None → success=False."""
    with patch("app.services.reminder_service.ReminderRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.soft_delete = AsyncMock(return_value=None)
        service = ReminderService(session)
        result = await service.delete_reminder(999, 1)
    assert result.success is False


async def test_delete_reminder_success(session, fake_reminder):
    """delete_reminder при soft_delete → fake_reminder → success=True."""
    with patch("app.services.reminder_service.ReminderRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.soft_delete = AsyncMock(return_value=fake_reminder)
        service = ReminderService(session)
        result = await service.delete_reminder(1, 1)
    assert result.success is True
    assert result.reminder is fake_reminder
