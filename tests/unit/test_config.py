"""Unit-тесты для Settings.parse_allowed_users."""
from app.config import Settings


def test_parse_allowed_users_from_list():
    """Вход: list[int] → frozenset."""
    result = Settings.parse_allowed_users([123, 456])
    assert result == frozenset({123, 456})


def test_parse_allowed_users_from_frozenset():
    """Вход: frozenset → frozenset без изменений."""
    result = Settings.parse_allowed_users(frozenset({789}))
    assert result == frozenset({789})


def test_parse_allowed_users_from_set():
    """Вход: set → frozenset."""
    result = Settings.parse_allowed_users({100, 200})
    assert result == frozenset({100, 200})


def test_parse_allowed_users_from_csv_string():
    """Вход: строка CSV → frozenset."""
    result = Settings.parse_allowed_users("111,222")
    assert result == frozenset({111, 222})


def test_parse_allowed_users_from_single_string():
    """Вход: одно число в строке → frozenset."""
    result = Settings.parse_allowed_users("42")
    assert result == frozenset({42})


def test_parse_allowed_users_strips_whitespace():
    """Вход: строка с пробелами → frozenset без пробелов."""
    result = Settings.parse_allowed_users(" 10 , 20 ")
    assert result == frozenset({10, 20})
