"""conftest.py — env vars ДОЛЖНЫ быть первыми строками, ДО любых import."""
import os

os.environ.setdefault("BOT_TOKEN", "0:AAtest_token_for_testing_only")
os.environ.setdefault("OWNER_ID", "123456789")
os.environ.setdefault("ALLOWED_USERS", "[123456789,987654321]")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_NAME", "familybot_test")
os.environ.setdefault("DB_USER", "familybot")
