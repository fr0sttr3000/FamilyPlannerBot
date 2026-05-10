"""Unit-тесты для TaskService."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.task_service import TaskService


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def fake_task():
    task = MagicMock()
    task.id = 1
    return task


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
