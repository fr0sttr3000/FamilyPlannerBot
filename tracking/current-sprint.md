# Current Sprint — FamilyPlannerBot
**Обновлено:** 2026-05-10

---

## Статус

| Sprint | Версия | Дата | Статус |
|--------|--------|------|--------|
| Sprint 3 | v1.2.0 | 2026-05-10 | ✅ CLOSED (CONDITIONAL GO) |
| Sprint 4 | v1.3.0 | — | 🔲 В планировании |

**Sprint 3 закрыт.** Все 5 Stories выполнены (19/19 SP). Вердикт QA — CONDITIONAL GO: 43/43 unit-тестов пройдено, UAT в живом Telegram ожидает проведения владельцем.

**Sprint 4 ещё не начат.** Требуется запуск s1-pm для формирования Sprint 4 Plan.

---

## Приоритеты Sprint 4 (топ-5)

| Приоритет | ID | Задача | SP | Тип | Обоснование |
|-----------|-----|--------|----|-----|-------------|
| 1 | US-24 | `/admin backup` — резервное копирование через бота (pg_dump) | 5 | Must | Перенесён из Sprint 3 (Stretch Goal); давно ожидает |
| 2 | US-25 | `/admin users` — список пользователей для владельца | 3 | Must | Must Have для admin-функционала v1.x |
| 3 | US-34 | Назначение напоминания @username | 5 | Could | Разблокирован реализацией US-33 в Sprint 3 |
| 4 | US-07 | История напоминаний `/history reminders` | 3 | Should | Backlog; дополняет /donetasks из Sprint 3 |
| 5 | US-12 | Уведомление при создании задачи | 3 | Should | Backlog; улучшает опыт назначения (US-33) |

**Суммарно топ-5:** 19 SP (укладывается в velocity 20 SP при 1 разработчике)

---

## Технический долг Sprint 3 → Sprint 4

| ID | Описание | Приоритет |
|----|----------|-----------|
| TD-01 | Ellipsis sentinel → `_UNSET = object()` в `task_repo.py` (mypy) | Medium |
| TD-02 | `_parse_scheduled_at()` → `app/utils/date_parser.py` (DRY) | Medium |
| TD-03 | AuthMiddleware: username TTL при смене в Telegram | Low |

---

## Open Issues для QA Sprint 4

| ID | Описание |
|----|---------|
| QA-OI-05 | TC-ASGN-06 race condition — автоматизировать параллельные callback-запросы |
| QA-OI-06 | users.username: проверить обновление при повторном /start |
| QA-OI-07 | Нагрузочное тестирование: NFR-SCAL-01 (20 одновременных пользователей) |
| QA-OI-08 | HTML parse_mode регрессия: Markdown-кейсы Sprint 1 |

---

## Действия для запуска Sprint 4

1. Запустить **s1-pm** → сформировать `PM-2026-05-10-sprint4.md` (план Sprint 4)
2. Запустить **s0-tracker** → `/sprint-init sprint-04`
3. Запустить **s4-dev** → реализация US-24, US-25 в первую очередь
4. Выполнить **UAT Sprint 3** (C-02, C-03) параллельно — получить sign-off владельца
