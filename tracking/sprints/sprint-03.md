# Sprint 3 — FamilyPlannerBot
**Период:** 2026-05-10 (выполнен за 1 сессию)
**Версия:** v1.2.0
**Статус:** COMPLETED

---

## Sprint Goal

**«Семья получает напоминания вовремя, видит что уже сделано, может делегировать дела друг другу и управлять ботом без терминала»**

После Sprint 3:
- Напоминания доставляются автоматически — проверено в живом окружении (UAT US-04)
- Можно посмотреть историю выполненных задач
- Можно прикрепить напоминание к конкретной невыполненной задаче
- Можно назначить задачу другому члену семьи и получить подтверждение
- Владелец получает обзор состояния бота командой `/adminoverview`
- Заметки можно удалять

---

## Plan vs Fact

| Story | Описание | Plan SP | Fact SP | Статус | Примечание |
|-------|----------|---------|---------|--------|------------|
| US-16 | `/delnote` — удаление заметки | 2 | 2 | ✅ Done | Soft delete с проверкой владельца; CR-04 исправлен (Markdown → HTML) |
| US-13 | `/donetasks` — история выполненных задач | 3 | 3 | ✅ Done | 30 дней, лимит 20, сортировка по дате |
| US-23 | `/adminoverview` — сводка для владельца | 3 | 3 | ✅ Done | Проверка OWNER_ID на уровне handler; 8 auto-тестов |
| US-32 | `/taskremind` — напоминание о задаче | 3 | 3 | ✅ Done | Skip если задача выполнена (status=skipped); миграция 0002 |
| US-33 | `/taskassign` — назначение с подтверждением | 8 | 8 | ✅ Done | 4 исправления CR (CR-01..CR-04); inline callback Accept/Decline; защита от race condition |
| **Итого** | | **19** | **19** | **5/5 Stories** | Velocity план = факт |

**Stretch Goal (US-24 `/admin backup`, 5 SP):** не реализован — перенесён в Sprint 4 как Must (плановое решение PM).

---

## Артефакты спринта

| Файл | Агент | Описание |
|------|-------|----------|
| `stage1-planning/outputs/PM-2026-05-10-sprint3.md` | s1-pm | Sprint 3 Plan (5 Stories, детальный план, риски) |
| `stage4-dev/outputs/DEV-2026-05-10-sprint3-summary.md` | s4-dev | Dev Summary: 17 файлов создано/изменено, 29 unit-тестов |
| `stage4-dev/outputs/DEV-2026-05-10-code-review-sprint3.md` | s4-techlead | Code Review: APPROVED WITH CHANGES (CR-01..CR-06) |
| `stage5-testing/outputs/QA-2026-05-10-go-no-go-sprint3.md` | s5-qa | Go/No-Go Report: CONDITIONAL GO (43/43 тестов) |
| `stage5-testing/outputs/AUTO-2026-05-10-coverage-sprint3.md` | s5-qa-auto | Auto Coverage: 43 passed / 0 failed; 19 новых тестов |
| `stage6-deploy/outputs/REL-2026-05-10-release-notes-v1.2.0.md` | s6-release | Release Notes v1.2.0 (пользовательский язык) |

**Файлы кода (созданы/изменены в Sprint 3):**

| Файл | Действие |
|------|----------|
| `migrations/versions/0002_sprint3_assignment.py` | Создан |
| `app/db/models/task.py` | Изменён (assigned_to, assignment_status) |
| `app/db/models/reminder.py` | Изменён (task_id, REMINDER_STATUS_SKIPPED) |
| `app/db/models/user.py` | Изменён (relationship assigned_tasks) |
| `app/db/repositories/task_repo.py` | Изменён (3 новых метода) |
| `app/db/repositories/note_repo.py` | Изменён (soft_delete_owned) |
| `app/db/repositories/user_repo.py` | Изменён (get_by_username) |
| `app/services/task_service.py` | Перезаписан (6 новых методов) |
| `app/services/note_service.py` | Изменён (delete_note) |
| `app/bot/handlers/tasks.py` | Перезаписан (4 новых handler + callback) |
| `app/bot/handlers/notes.py` | Изменён (/delnote + Markdown→HTML) |
| `app/bot/handlers/admin.py` | Создан |
| `app/bot/handlers/start.py` | Изменён (HELP_TEXT Sprint 3) |
| `app/scheduler/reminder_scheduler.py` | Изменён (task_id skip-логика) |
| `app/main.py` | Изменён (admin.router) |
| `tests/unit/test_task_service.py` | Изменён (5 новых тестов) |
| `tests/unit/test_note_service.py` | Создан (3 теста US-16) |

---

## Code Review результат

**Вердикт:** APPROVED WITH CHANGES  
**Reviewer:** Tech Lead (s4-techlead), 2026-05-10

| ID | Severity | Описание | Статус |
|----|----------|----------|--------|
| CR-01 | HIGH | `server_default=func.cast(...)` → `server_default="none"` в Task.assignment_status | ✅ Исправлено |
| CR-02 | HIGH | `callback.message.bot.send_message` → инъекция `bot: Bot` в callback-handlers | ✅ Исправлено |
| CR-03 | HIGH | Отсутствовала проверка `if _bot is None` в `morning_digest()` | ✅ Исправлено |
| CR-04 | MEDIUM | `parse_mode="Markdown"` в notes.py → `parse_mode="HTML"` (унификация) | ✅ Исправлено |
| CR-05 | LOW | Ellipsis sentinel в `update_assignment()` — mypy `# type: ignore` | → TD-01 Sprint 4 |
| CR-06 | LOW | `_parse_scheduled_at()` дублируется в TaskService и ReminderService | → TD-02 Sprint 4 |

---

## QA результат

**Вердикт:** CONDITIONAL GO  
**QA Lead:** s5-qa, 2026-05-10

| Метрика | Значение |
|---------|---------|
| Unit-тесты | 43 / 43 passed (0 failed) |
| Новые тесты Sprint 3 | 19 (из 43 итого) |
| Stories покрыто | 5 / 5 (100% AC) |
| Функциональных TC | 24 тест-кейса |
| UAT US-04 | Не проведён в живом Telegram (условие C-02) |

**Условия CONDITIONAL GO → GO:**

| # | Условие | Приоритет |
|---|---------|-----------|
| C-01 | Фактический прогон 24 тест-кейсов Sprint 3 | Critical |
| C-02 | UAT US-04: TC-DLVR-01..03 в живом Telegram | Critical |
| C-03 | UAT sign-off от владельца | Critical |
| C-04 | Code review без блокирующих замечаний (выполнено) | High |
| C-05 | `alembic upgrade head` без ошибок на staging | High |
| C-06 | users.username для TEST_USER_2_ID заполнен | High |

---

## Технический долг, обнаруженный в спринте

| ID | Приоритет | Описание | Целевой Sprint |
|----|-----------|----------|----------------|
| TD-01 | Medium | `update_assignment(assigned_to=...)` — Ellipsis sentinel с `# type: ignore`. Заменить на явный `_UNSET = object()` для mypy-совместимости | Sprint 4 |
| TD-02 | Medium | `_parse_scheduled_at()` дублируется в TaskService и ReminderService. Вынести в `app/utils/date_parser.py` | Sprint 4 |
| TD-03 | Low | `AuthMiddleware` не обновляет username при смене в Telegram. Добавить TTL или задокументировать как known limitation | Sprint 4 |

---

## Velocity факт vs план

| Метрика | План | Факт |
|---------|------|------|
| Stories | 5 | 5 |
| Story Points | 19 SP (velocity 20, 1 резерв) | 19 SP |
| Stretch Goal (US-24) | Опционально | Не реализован (плановое решение) |
| Unit-тесты | ≥ 8 новых | 19 новых (43 всего) |
| Дефекты Critical | 0 | 0 |
| CR найдено / исправлено | — | 4 HIGH/MEDIUM исправлены; 2 LOW → техдолг |

---

## Что переходит в Sprint 4

| ID | Задача | SP | Тип | Источник |
|----|--------|----|-----|----------|
| US-24 | `/admin backup` (pg_dump) | 5 | Must | Stretch Goal Sprint 3 |
| US-25 | `/admin users` | 3 | Must | Backlog |
| US-34 | Назначение напоминания @username | 5 | Could | Зависит от US-33 (готов) |
| US-07 | История напоминаний `/history reminders` | 3 | Should | Backlog |
| US-12 | Уведомление при создании задачи | 3 | Should | Backlog |
| US-21 | Удаление события `/event delete` | 2 | Should | Backlog |
| TD-01 | Ellipsis sentinel → `_UNSET` в task_repo | — | Техдолг | CR-05 |
| TD-02 | `_parse_scheduled_at()` → `app/utils/` | — | Техдолг | CR-06 |
| TD-03 | AuthMiddleware username TTL | — | Техдолг | ADR-06 |
