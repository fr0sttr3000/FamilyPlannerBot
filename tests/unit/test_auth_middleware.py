"""Unit-тесты для AuthMiddleware."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.bot.middlewares.auth import AuthMiddleware


def make_user(user_id: int) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.username = "testuser"
    user.first_name = "Test"
    return user


async def test_unauthorized_user_is_blocked():
    """Неавторизованный пользователь → handler не вызван, result is None."""
    middleware = AuthMiddleware()
    handler = AsyncMock(return_value="ok")
    event = MagicMock()
    data = {"event_from_user": make_user(99999)}

    mock_settings = MagicMock()
    mock_settings.allowed_users = frozenset({123456})

    with patch("app.bot.middlewares.auth.settings", mock_settings):
        result = await middleware(handler, event, data)

    assert result is None
    handler.assert_not_called()


async def test_authorized_user_passes():
    """Авторизованный пользователь → handler вызван один раз, result == 'ok'."""
    middleware = AuthMiddleware()
    handler = AsyncMock(return_value="ok")
    event = MagicMock()
    data = {"event_from_user": make_user(123456), "session": None}

    mock_settings = MagicMock()
    mock_settings.allowed_users = frozenset({123456})

    with patch("app.bot.middlewares.auth.settings", mock_settings):
        result = await middleware(handler, event, data)

    assert result == "ok"
    handler.assert_called_once()


async def test_no_event_from_user_passes():
    """Нет event_from_user в data → handler вызван (пропустить без проверки)."""
    middleware = AuthMiddleware()
    handler = AsyncMock(return_value="ok")
    event = MagicMock()
    data = {}

    result = await middleware(handler, event, data)

    assert result == "ok"
    handler.assert_called_once()
