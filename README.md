# FamilyPlannerBot

Telegram-бот семейного планирования. Общие задачи, заметки, напоминания и календарь для всей семьи в одном месте.

## Назначение

FamilyPlannerBot — приватный бот для группы до 20 человек. Доступ ограничен whitelist Telegram ID в файле `.env`. Бот разворачивается на личном сервере или VPS через Docker Compose.

## Архитектура

```
Telegram API
     |
     | HTTPS Long Polling
     v
[Bot Container: Python 3.11 / aiogram 3.x]
     |
     | SQL (asyncpg, внутренняя Docker-сеть)
     v
[DB Container: PostgreSQL 15]
     |
     v
[pg_data Volume] — персистентные данные
[backups Volume] — дампы pg_dump
```

**Слои приложения:**

| Слой | Директория | Ответственность |
|------|-----------|-----------------|
| Handlers | `app/bot/handlers/` | Принять Update, вызвать сервис, ответить |
| Middleware | `app/bot/middlewares/` | Auth (whitelist), DB Session injection |
| Services | `app/services/` | Бизнес-логика, валидация |
| Repositories | `app/db/repositories/` | SQL-запросы через SQLAlchemy async |
| Models | `app/db/models/` | ORM-модели (SQLAlchemy DeclarativeBase) |
| Scheduler | `app/scheduler/` | APScheduler (доставка напоминаний — Sprint 2) |

## Структура директорий

```
app/
├── bot/
│   ├── handlers/       # /start, /tasks, /notes, /reminders, /calendar
│   └── middlewares/    # AuthMiddleware, DBSessionMiddleware
├── db/
│   ├── models/         # SQLAlchemy ORM-модели
│   └── repositories/   # Слой доступа к данным
├── services/           # Бизнес-логика
├── scheduler/          # APScheduler setup
├── config.py           # pydantic-settings (из .env)
└── main.py             # Точка входа
migrations/             # Alembic миграции
```

## Локальное окружение

### Предварительные требования

- Docker Engine >= 24.0
- Docker Compose >= 2.0

### Запуск

```bash
# 1. Скопировать шаблон конфигурации
cp .env.example .env

# 2. Заполнить .env (BOT_TOKEN, ALLOWED_USERS, DB_PASSWORD)
nano .env

# 3. Запустить
docker compose up -d

# 4. Проверить статус
docker compose ps
docker compose logs -f bot
```

### Остановка

```bash
docker compose down
```

### Просмотр логов

```bash
docker compose logs -f bot          # tail логов
docker compose logs --since 1h bot  # за последний час
```

## Переменные окружения

Все переменные описаны в `.env.example`.

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `BOT_TOKEN` | Токен бота от @BotFather | `123:ABC...` |
| `OWNER_ID` | Telegram ID владельца | `123456789` |
| `ALLOWED_USERS` | ID авторизованных пользователей | `123456789,987654321` |
| `DB_PASSWORD` | Пароль PostgreSQL | `strong_password` |
| `TIMEZONE` | Часовой пояс | `Europe/Moscow` |

## Запуск тестов

```bash
# Установить зависимости для разработки
pip install -r requirements.txt pytest pytest-asyncio

# Запустить тесты
pytest tests/ -v
```

## Миграции базы данных

```bash
# Применить все миграции
docker compose exec bot alembic upgrade head

# Откатить последнюю миграцию
docker compose exec bot alembic downgrade -1

# Текущая версия схемы
docker compose exec bot alembic current
```

## Подробная документация

- `CONTRIBUTING.md` — как добавлять новые функции
- `.env.example` — все переменные окружения с описанием
