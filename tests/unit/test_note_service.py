"""Unit-тесты для NoteService — Sprint 3 (US-16)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.note_service import NoteService


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def fake_note_owner():
    """Заметка, принадлежащая пользователю с ID 1."""
    note = MagicMock()
    note.id = 10
    note.user_id = 1
    note.text = "Тестовая заметка"
    note.deleted_at = None
    return note


@pytest.fixture
def fake_note_other():
    """Заметка, принадлежащая другому пользователю (ID 2)."""
    note = MagicMock()
    note.id = 11
    note.user_id = 2
    note.text = "Чужая заметка"
    note.deleted_at = None
    return note


async def test_delete_note_not_owner(session, fake_note_other):
    """delete_note с чужой заметкой → success=False, ошибка о правах."""
    with patch("app.services.note_service.NoteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        # soft_delete_owned возвращает None для чужой заметки
        mock_repo.soft_delete_owned = AsyncMock(return_value=None)

        service = NoteService(session)
        result = await service.delete_note(note_id=11, user_id=1)

    assert result.success is False
    assert result.error is not None
    assert "нет прав" in result.error or "не найдена" in result.error


async def test_delete_note_not_found(session):
    """delete_note с несуществующим ID → success=False."""
    with patch("app.services.note_service.NoteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.soft_delete_owned = AsyncMock(return_value=None)

        service = NoteService(session)
        result = await service.delete_note(note_id=9999, user_id=1)

    assert result.success is False
    assert result.error is not None


async def test_delete_note_success(session, fake_note_owner):
    """delete_note своей заметки → success=True, note возвращена."""
    with patch("app.services.note_service.NoteRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.soft_delete_owned = AsyncMock(return_value=fake_note_owner)

        service = NoteService(session)
        result = await service.delete_note(note_id=10, user_id=1)

    assert result.success is True
    assert result.note is fake_note_owner
