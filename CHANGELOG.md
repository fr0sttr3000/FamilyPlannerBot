# Changelog

Все значимые изменения FamilyPlannerBot документируются здесь.

Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/)
Версионирование: [Semantic Versioning](https://semver.org/lang/ru/)

---

## [1.2.1] — 2026-05-11

### Fixed
- ORM-модели: все datetime-колонки переведены на `TIMESTAMP(timezone=True)` через `sqlalchemy.dialects.postgresql.TIMESTAMP`
- Alembic-миграция `0003_timestamp_timezone`: `ALTER COLUMN` для 14 колонок в 5 таблицах (users, tasks, reminders, notes, events)
- Устраняет `TypeError: can't compare offset-naive and offset-aware datetimes` в `reminder_scheduler.py` при работе с asyncpg

---

## [1.2.0] — 2026-05-10

### Added
- `/delnote <ID>` — удаление своей заметки по номеру (US-16); проверка владельца на двух уровнях: `NoteRepository.soft_delete_owned()` и `NoteService.delete_note()`
- `/donetasks` — история выполненных задач за последние 30 дней, лимит 20 записей, сортировка по `completed_at` DESC (US-13)
- `/adminoverview` — сводка состояния для владельца бота: количество активных задач, 5 ближайших напоминаний, события на текущую неделю; проверка `settings.owner_id` (US-23)
- `/taskremind <ID> <YYYY-MM-DD> <HH:MM>` — создание напоминания, привязанного к конкретной задаче; автоматический пропуск (статус `skipped`) если задача выполнена или удалена к моменту срабатывания (US-32)
- `/taskassign <ID> @username` — назначение задачи члену семьи с отправкой inline-уведомления и кнопками «Принять» / «Отклонить» (US-33)
- Callback handlers `assign_accept:{task_id}:{assigner_id}` и `assign_decline:{task_id}:{assigner_id}` — обработка ответа адресата, инвалидация кнопок, уведомление создателя задачи (US-33)
- `AdminService.get_overview()` — новый сервис с `AdminOverview` dataclass; агрегация данных для `/adminoverview`
- `UserRepository.get_by_username()` — поиск пользователя по `@username` (case-insensitive через `func.lower()`)
- `TaskRepository.get_by_id_active()`, `get_completed()`, `update_assignment()` — новые методы репозитория
- `NoteRepository.soft_delete_owned()` — soft delete с проверкой владельца
- Константы `ASSIGNMENT_STATUS_NONE / PENDING / ACCEPTED / DECLINED` в `task.py`
- Константа `REMINDER_STATUS_SKIPPED` в `reminder.py`
- Индикатор назначения в `/tasks`: `[ожидает @username]` и `[принята @username]`
- Миграция Alembic `0002_sprint3_assignment`: поля `reminders.task_id`, `tasks.assigned_to`, `tasks.assignment_status` с индексами и FK
- 8 новых unit-тестов (Sprint 3): `test_note_service.py` (3 теста, US-16), `test_task_service.py` +5 тестов (US-32 и US-33)

### Changed
- `tasks.py` handlers переведены с Markdown на HTML (`parse_mode="HTML"`) — безопаснее при произвольном тексте задач
- `notes.py` handlers переведены с Markdown на HTML (CR-04: `parse_mode="Markdown"` → `parse_mode="HTML"`, разметка `*...*` → `<b>...</b>`, `_..._` → `<i>...</i>`)
- `TaskService` расширен методами `get_completed_tasks()`, `create_task_reminder()`, `assign_task()`, `accept_assignment()`, `decline_assignment()`, `get_task_by_id()`, `get_active_task_by_id()`
- `NoteService` расширен методом `delete_note()` с проверкой прав
- `reminder_scheduler._deliver_pending()` расширен логикой пропуска напоминаний: если связанная задача выполнена или удалена — статус `skipped`, уведомление не отправляется
- `app/main.py` — зарегистрирован `admin.router`
- `start.py` HELP_TEXT дополнен командами Sprint 3 (`/delnote`, `/donetasks`, `/adminoverview`, `/taskremind`, `/taskassign`)
- `TaskRepository.get_active()` расширен `selectinload(Task.assignee)` — нет N+1 запросов при отображении списка с индикатором назначения

### Fixed
- CR-01: `task.py` — `server_default=func.cast(ASSIGNMENT_STATUS_NONE, String)` заменён на `server_default="none"` (некорректный DDL через `func.cast` в ORM-модели)
- CR-02: `tasks.py` — `callback.message.bot.send_message(...)` заменён на инъекцию `bot: Bot` как параметра callback-handler (канонический паттерн aiogram 3.x; `callback.message.bot` может быть `None`)
- CR-03: `reminder_scheduler.py` — добавлена проверка `if _bot is None` в `morning_digest()` (аналогичная проверка уже была в `_deliver_pending()`; пропуск вызывал `AttributeError` при неинициализированном боте)
- CR-04: `notes.py` — все handlers переведены с Markdown на HTML (Markdown v1 ломается при наличии `_`, `*`, `` ` `` в тексте заметки без экранирования)

---

## [1.1.0] — 2026-05-09

### Added
- APScheduler с SQLAlchemy JobStore — задания планировщика сохраняются в PostgreSQL, не теряются при рестарте контейнера (US-04)
- `deliver_reminders` job — интервал 1 минута; доставка pending-напоминаний всем адресатам через `bot.send_message`
- `morning_digest` job — cron 08:00 МСК; утренняя рассылка событий и напоминаний на текущий день всем пользователям из `allowed_users`
- `watchdog` job — интервал 10 минут; авторестановка пропущенных напоминаний (статус `pending`, `scheduled_at` в прошлом)
- `heartbeat` job — интервал 5 минут; запись в лог подтверждения работоспособности планировщика
- 21 unit-тест для сервисного слоя (`tests/unit/`) — покрытие `TaskService`, `NoteService`, `ReminderService`, `EventService`

### Changed
- `reminder_scheduler.py` полностью переписан: заглушка Sprint 1 заменена на рабочий AsyncIOScheduler с 4 зарегистрированными jobs
- `app/main.py` — scheduler инициализируется и стартует вместе с ботом; `init_scheduler(bot)` передаёт экземпляр бота в планировщик

---

## [1.0.0] — 2026-05-09

### Added
- Первый рабочий выпуск (MVP)
- Авторизация по белому списку: `AuthMiddleware` проверяет Telegram ID через `frozenset(ALLOWED_USERS)`, O(1); UPSERT записи в таблицу `users` при каждом запросе
- `/addtask <текст>` — создание задачи; `/tasks` — список активных задач; `/donetask <ID>` — отметка выполненной; `/deltask <ID>` — soft delete
- `/addnote <текст>` — создание заметки; `/notes` — список активных заметок (лимит 50)
- `/addreminder <YYYY-MM-DD> <HH:MM> <текст>` — создание напоминания с парсингом даты; `/reminders` — список активных напоминаний; `/delreminder <ID>` — soft delete
- `/addevent <YYYY-MM-DD> <текст>` — добавление события в календарь; `/calendar` — события на ближайшие дни (лимит 30)
- `/start` — приветствие и базовая авторизация; `/help` — полный список команд с примерами (≤ 30 строк)
- Docker Compose: сервисы `bot` + `db` (postgres:15-alpine); pinned-теги образов; named volumes (`pg_data`, `backups`); healthcheck для PostgreSQL; non-root user `botuser` в контейнере бота
- Alembic миграции: `0001_initial` — 5 таблиц (`users`, `tasks`, `notes`, `reminders`, `events`) + 12 индексов (включая partial indexes для soft delete); `run_migrations()` вызывается автоматически при старте бота
- Трёхслойная архитектура: Handlers → Services → Repositories; `DBSessionMiddleware` инъектирует `AsyncSession`; `BaseRepository[T]` с generic-типизацией
- Soft delete для всех сущностей: поле `deleted_at IS NULL` в partial indexes
- `scripts/backup.sh` — pg_dump в `./backups/` (сжатый `.sql.gz`); `scripts/restore.sh` — восстановление с подтверждением
- Документация: `README.md`, `INSTALL-GUIDE.md`, `OWNER-GUIDE.md`, `CONTRIBUTING.md`, `.env.example`
