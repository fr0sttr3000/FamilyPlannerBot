"""conftest.py — загружает тестовое окружение из .env.test ДО любых import."""
import os
from pathlib import Path


def _load_env_test() -> None:
    env_file = Path(__file__).parent.parent / ".env.test"
    if not env_file.exists():
        raise FileNotFoundError(
            ".env.test не найден. Скопируйте .env.test.example в .env.test "
            "и заполните тестовыми значениями."
        )
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_test()
