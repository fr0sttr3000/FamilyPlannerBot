"""Unit-тесты для TaskService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.task import ASSIGNMENT_STATUS_PENDING
from app.services.task_service import TaskService


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def fake_task():
    task = MagicMock()
    task.id = 1
    task.text = "Купить молоко"
    task.assignment_status = "none"
    task.assigned_to = None
    return task


# ────────────────────────── Sprint 1/2 тесты ──────────────────────────


async def test_create_task_empty_text(session):
    """create_task с пустым текстом → success=False, error содержит 'пустым'."""
    with patch("app.services.task_service.TaskRepository"):
        service = TaskService(session)
        result = await service.create_task(user_id=1, text="  ")
    assert result.success is False
    assert "пустым" in result.error


async def test_create_task_too_long_text(session):
    """create_task с длинным текстом → success=False, error содержит 'длинный'."""
    with patch("app.services.task_service.TaskRepository"):
        service = TaskService(session)
        result = await service.create_task(user_id=1, text="x" * 501)
    assert result.success is False
    assert "длинный" in result.error


async def test_create_task_success(session, fake_task):
    """create_task с валидным текстом → success=True, task — мок-объект."""
    with patch("app.services.task_service.TaskRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.save = AsyncMock(return_value=fake_task)
        service = TaskService(session)
        result = await service.create_task(user_id=1, text="Buy milk")
    assert result.success is True
    assert result.task is fake_task


async def test_complete_task_not_found(session):
    """complete_task при mark_done → None → success=False, '999' в error."""
    with patch("app.services.task_service.TaskRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.mark_done = AsyncMock(return_value=None)
        service = TaskService(session)
        result = await service.complete_task(task_id=999, user_id=1)
    assert result.success is False
    assert "999" in result.error


async def test_complete_task_success(session, fake_task):
    """complete_task при mark_done → fake_task → success=True."""
    with patch("app.services.task_service.TaskRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.mark_done = AsyncMock(return_value=fake_task)
        service = TaskService(session)
        result = await service.complete_task(task_id=5, user_id=1)
    assert result.success is True
    assert result.task is fake_task


async def test_delete_task_not_found(session):
    """delete_task при soft_delete → None → success=False."""
    with patch("app.services.task_service.TaskRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.soft_delete = AsyncMock(return_value=None)
        service = TaskService(session)
        result = await service.delete_task(task_id=999, user_id=1)
    assert result.success is False


async def test_delete_task_success(session, fake_task):
    """delete_task при soft_delete → fake_task → success=True."""
    with patch("app.services.task_service.TaskRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.soft_delete = AsyncMock(return_value=fake_task)
        service = TaskService(session)
        result = await service.delete_task(task_id=7, user_id=1)
    assert result.success is True
    assert result.task is fake_task


# ────────────────────────── Sprint 3 — US-32 тесты ──────────────────────────


async def test_create_task_reminder_task_not_found(session):
    """create_task_reminder с несуществующей задачей → success=False."""
    with patch("app.services.task_service.TaskRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_id_active = AsyncMock(return_value=None)
        service = TaskService(session)
        result = await service.create_task_reminder(
            task_id=9999, user_id=1, date_str="2026-06-01", time_str="10:00"
        )
    assert result.success is False
    assert result.error is not None
    assert "не найдена" in result.error


async def test_create_task_reminder_success(session, fake_task):
    """create_task_reminder с активной задачей и корректной датой → success=True, reminder создан."""
    fake_reminder = MagicMock()
    fake_reminder.id = 42

    with (
        patch("app.services.task_service.TaskRepository") as MockTaskRepo,
        patch("app.services.task_service.ReminderRepository") as MockReminderRepo,
    ):
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=fake_task)

        reminder_repo = MockReminderRepo.return_value
        reminder_repo.save = AsyncMock(return_value=fake_reminder)

        service = TaskService(session)
        result = await service.create_task_reminder(
            task_id=1, user_id=1, date_str="2026-06-01", time_str="10:00"
        )

    assert result.success is True
    assert result.task is fake_task


# ────────────────────────── Sprint 3 — US-33 тесты ──────────────────────────


async def test_assign_task_username_not_found(session, fake_task):
    """assign_task с несуществующим @username → success=False, ошибка о пользователе."""
    with (
        patch("app.services.task_service.TaskRepository") as MockTaskRepo,
        patch("app.services.task_service.UserRepository") as MockUserRepo,
    ):
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=fake_task)

        user_repo = MockUserRepo.return_value
        user_repo.get_by_username = AsyncMock(return_value=None)

        service = TaskService(session)
        result = await service.assign_task(
            task_id=1, assigner_user_id=100, target_username="@unknown"
        )

    assert result.success is False
    assert result.error is not None
    assert "не найден" in result.error


async def test_assign_task_already_pending(session):
    """assign_task когда задача уже в статусе pending → success=False."""
    pending_task = MagicMock()
    pending_task.id = 1
    pending_task.assignment_status = ASSIGNMENT_STATUS_PENDING

    with patch("app.services.task_service.TaskRepository") as MockTaskRepo:
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=pending_task)

        service = TaskService(session)
        result = await service.assign_task(
            task_id=1, assigner_user_id=100, target_username="@masha"
        )

    assert result.success is False
    assert result.error is not None
    assert "ожидает" in result.error


async def test_assign_task_success(session, fake_task):
    """assign_task с корректными данными → success=True, target_user_id в result."""
    fake_target = MagicMock()
    fake_target.id = 200
    fake_target.username = "masha"

    updated_task = MagicMock()
    updated_task.id = 1

    with (
        patch("app.services.task_service.TaskRepository") as MockTaskRepo,
        patch("app.services.task_service.UserRepository") as MockUserRepo,
    ):
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=fake_task)
        task_repo.update_assignment = AsyncMock(return_value=updated_task)

        user_repo = MockUserRepo.return_value
        user_repo.get_by_username = AsyncMock(return_value=fake_target)

        service = TaskService(session)
        result = await service.assign_task(
            task_id=1, assigner_user_id=100, target_username="@masha"
        )

    assert result.success is True
    assert result.target_user_id == 200


async def test_assign_task_self_assign(session, fake_task):
    """assign_task когда assigner пытается назначить задачу самому себе → success=False."""
    fake_self = MagicMock()
    fake_self.id = 100  # тот же ID, что и assigner_user_id

    with (
        patch("app.services.task_service.TaskRepository") as MockTaskRepo,
        patch("app.services.task_service.UserRepository") as MockUserRepo,
    ):
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=fake_task)

        user_repo = MockUserRepo.return_value
        user_repo.get_by_username = AsyncMock(return_value=fake_self)

        service = TaskService(session)
        result = await service.assign_task(
            task_id=1, assigner_user_id=100, target_username="@self"
        )

    assert result.success is False
    assert result.error is not None
    assert "себе" in result.error


# ────────────────────────── Sprint 3 — дополнительные тесты ──────────────────────────


async def test_assign_task_not_found(session):
    """assign_task когда задача не найдена → success=False, ошибка о задаче."""
    with patch("app.services.task_service.TaskRepository") as MockTaskRepo:
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=None)

        service = TaskService(session)
        result = await service.assign_task(
            task_id=9999, assigner_user_id=100, target_username="@masha"
        )

    assert result.success is False
    assert result.error is not None
    assert "9999" in result.error


async def test_create_task_reminder_task_completed(session):
    """create_task_reminder для уже выполненной задачи → success=False.

    get_by_id_active возвращает None, т.к. репозиторий фильтрует completed_at IS NULL.
    """
    with patch("app.services.task_service.TaskRepository") as MockTaskRepo:
        task_repo = MockTaskRepo.return_value
        # Активный метод get_by_id_active возвращает None для выполненной задачи
        task_repo.get_by_id_active = AsyncMock(return_value=None)

        service = TaskService(session)
        result = await service.create_task_reminder(
            task_id=5, user_id=1, date_str="2026-06-01", time_str="10:00"
        )

    assert result.success is False
    assert result.error is not None
    # Задача выполнена — get_by_id_active возвращает None → "не найдена или уже выполнена"
    assert "найдена" in result.error or "выполнена" in result.error


async def test_create_task_reminder_invalid_date(session, fake_task):
    """create_task_reminder с невалидным форматом даты → success=False, ошибка формата."""
    with patch("app.services.task_service.TaskRepository") as MockTaskRepo:
        task_repo = MockTaskRepo.return_value
        task_repo.get_by_id_active = AsyncMock(return_value=fake_task)

        service = TaskService(session)
        result = await service.create_task_reminder(
            task_id=1, user_id=1, date_str="invalid-date", time_str="99:99"
        )

    assert result.success is False
    assert result.error is not None
    # Ошибка парсинга даты — содержит подсказку по формату
    assert "формат" in result.error.lower() or "пример" in result.error.lower()


async def test_accept_assignment_success(session):
    """accept_assignment вызывает update_assignment со статусом 'accepted' и commit."""
    with patch("app.services.task_service.TaskRepository") as MockTaskRepo:
        task_repo = MockTaskRepo.return_value
        task_repo.update_assignment = AsyncMock(return_value=None)

        service = TaskService(session)
        await service.accept_assignment(task_id=1)

    task_repo.update_assignment.assert_awaited_once()
    call_kwargs = task_repo.update_assignment.call_args.kwargs
    assert call_kwargs.get("task_id") == 1
    assert call_kwargs.get("assignment_status") == "accepted"
    session.commit.assert_awaited_once()


async def test_decline_assignment_success(session):
    """decline_assignment вызывает update_assignment со статусом 'declined' и сбрасывает assigned_to."""
    with patch("app.services.task_service.TaskRepository") as MockTaskRepo:
        task_repo = MockTaskRepo.return_value
        task_repo.update_assignment = AsyncMock(return_value=None)

        service = TaskService(session)
        await service.decline_assignment(task_id=2)

    task_repo.update_assignment.assert_awaited_once()
    call_kwargs = task_repo.update_assignment.call_args.kwargs
    assert call_kwargs.get("task_id") == 2
    assert call_kwargs.get("assignment_status") == "declined"
    assert call_kwargs.get("assigned_to") is None
    session.commit.assert_awaited_once()
