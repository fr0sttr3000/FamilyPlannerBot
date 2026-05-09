# CONTRIBUTING.md — Руководство разработчика

## Содержание

1. [Структура handlers / services / models](#структура)
2. [Как добавить новую команду бота](#новая-команда)
3. [Как добавить новую таблицу в БД](#новая-таблица)
4. [Соглашения по именованию и стилю](#стиль)
5. [Сборка и публикация Docker-образа](#docker)
6. [Откат версии](#откат)

---

## Структура handlers / services / models {#структура}

Приложение разделено на слои с чёткими границами ответственности:

```
Handler → Service → Repository → Model
```

- **Handler** (`app/bot/handlers/`): парсит текст команды, вызывает сервис, формирует ответ. Не содержит бизнес-логику.
- **Service** (`app/services/`): валидация данных, бизнес-правила, оркестрация репозиториев. Не зависит от aiogram.
- **Repository** (`app/db/repositories/`): только SQL-запросы через SQLAlchemy async. Не содержит логику.
- **Model** (`app/db/models/`): SQLAlchemy ORM, только column definitions.

**Правила:**
- Handler не обращается к репозиторию напрямую — только через сервис.
- Сервис не импортирует ничего из `aiogram`.
- Репозиторий не содержит `if/else` бизнес-логики.

---

## Как добавить новую команду бота {#новая-команда}

Пример: добавляем команду `/shoppinglist` (список покупок).

### Шаг 1. Создать сервис

```python
# app/services/shopping_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.task_repo import TaskRepository  # или новый репозиторий

class ShoppingService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def get_list(self) -> list:
        # бизнес-логика здесь
        ...
```

### Шаг 2. Создать handler

```python
# app/bot/handlers/shopping.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.shopping_service import ShoppingService

router = Router(name="shopping")

@router.message(Command("shoppinglist"))
async def shopping_list_handler(message: Message, session: AsyncSession) -> None:
    service = ShoppingService(session)
    items = await service.get_list()
    # форматировать и отправить ответ
```

### Шаг 3. Зарегистрировать router в main.py

```python
# app/main.py
from app.bot.handlers import shopping  # добавить импорт

def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    # ...существующие routers...
    dp.include_router(shopping.router)  # добавить строку
    return dp
```

### Шаг 4. Добавить команду в /help

```python
# app/bot/handlers/start.py — добавить строку в HELP_TEXT
```

---

## Как добавить новую таблицу в БД {#новая-таблица}

Пример: добавляем таблицу `shopping_items`.

### Шаг 1. Создать модель

```python
# app/db/models/shopping_item.py
from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base

class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # ...
```

### Шаг 2. Импортировать модель в `__init__.py`

```python
# app/db/models/__init__.py
from app.db.models.shopping_item import ShoppingItem
```

### Шаг 3. Создать миграцию

```bash
# Alembic сгенерирует миграцию автоматически по изменениям в моделях
docker compose exec bot alembic revision --autogenerate -m "add_shopping_items"

# Проверить сгенерированный файл в migrations/versions/
# Применить
docker compose exec bot alembic upgrade head
```

### Шаг 4. Создать репозиторий

```python
# app/db/repositories/shopping_repo.py
from app.db.repositories.base import BaseRepository
from app.db.models.shopping_item import ShoppingItem

class ShoppingRepository(BaseRepository[ShoppingItem]):
    def __init__(self, session):
        super().__init__(session, ShoppingItem)
    # специализированные методы...
```

---

## Соглашения по именованию и стилю {#стиль}

### Именование файлов

| Тип | Шаблон | Пример |
|-----|--------|--------|
| Handler | `{domain}.py` | `tasks.py` |
| Service | `{domain}_service.py` | `task_service.py` |
| Repository | `{domain}_repo.py` | `task_repo.py` |
| Model | `{entity}.py` | `task.py` |
| Миграция | `{NNNN}_{описание}.py` | `0002_add_events.py` |

### Правила кода

- Функции: максимум 20 строк (SRP)
- Cyclomatic complexity: не более 10
- Нет магических чисел — только константы
- Все строки ответов бота: на **русском языке**
- Docstrings на всех публичных функциях и классах
- Все DB-операции через SQLAlchemy ORM (не raw SQL)
- Логирование: `logger = logging.getLogger(__name__)`

### Константы

```python
# Плохо
if len(tasks) > 100:
    ...

# Хорошо
ACTIVE_TASKS_LIMIT = 100
if len(tasks) > ACTIVE_TASKS_LIMIT:
    ...
```

### Обработка ошибок в handlers

```python
@router.message(Command("mycommand"))
async def my_handler(message: Message, session: AsyncSession) -> None:
    if message.from_user is None:
        return
    try:
        service = MyService(session)
        result = await service.do_something()
        await message.answer("Успешно!")
    except Exception:
        logger.exception("Ошибка в /mycommand user=%d", message.from_user.id)
        await message.answer("Не удалось выполнить команду. Попробуйте позже.")
```

---

## Сборка и публикация Docker-образа {#docker}

### Локальная сборка

```bash
# Собрать образ
docker build -t familyplannerbot:v1.1.0 .

# Проверить что секреты не попали в образ
docker history familyplannerbot:v1.1.0 | grep -i token
# Должна быть пустая строка
```

### Обновление на сервере

```bash
# Только бот (без пересоздания БД)
docker compose up -d --no-deps --build bot

# Все сервисы
docker compose up -d --build
```

### Публикация в registry (опционально)

```bash
# Тегировать и запушить
docker tag familyplannerbot:v1.1.0 your-registry/familyplannerbot:v1.1.0
docker push your-registry/familyplannerbot:v1.1.0
```

---

## Откат версии {#откат}

### Откат кода

```bash
# Откатить к предыдущему образу
docker compose down
docker tag familyplannerbot:v1.0.0 familyplannerbot:latest
docker compose up -d
```

### Откат миграции БД

```bash
# Откатить одну миграцию
docker compose exec bot alembic downgrade -1

# Откатить до конкретной ревизии
docker compose exec bot alembic downgrade 0001_initial
```

> **Предупреждение:** откат миграции может привести к потере данных.
> Всегда делайте `pg_dump` перед откатом.

```bash
# Создать бэкап перед откатом
docker exec fpb_db pg_dump -U $DB_USER $DB_NAME > backup_before_rollback.sql
```
