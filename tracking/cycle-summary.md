# Cycle Summary — FamilyPlannerBot
**Обновлено:** 2026-05-10

---

## Сводная таблица спринтов

| Sprint | Версия | Дата | Stories | SP | Тесты | Статус |
|--------|--------|------|---------|----|-------|--------|
| Sprint 1 | v1.0.0 | 2026-05-09 | 8 Must + 5 stretch | 20 | — | Released |
| Sprint 2 | v1.1.0 | 2026-05-09 | infra + tests | — | 21/21 | Released |
| Sprint 3 | v1.2.0 | 2026-05-10 | 5 | 19 | 43/43 | CONDITIONAL GO |

---

## Детали по спринтам

### Sprint 1 — v1.0.0 (2026-05-09)
**Ключевые итоги:** Базовый функционал бота. 8 Must Stories: `/start`, `/tasks` (CRUD), `/notes` (CRUD), `/reminders` (CRUD), `/calendar`. 5 Stretch goals реализованы. Авторизация через белый список (AuthMiddleware).

**Артефакты:** `stage1-planning/outputs/`, `stage2-requirements/outputs/`, `stage3-design/outputs/`, `stage4-dev/outputs/`

---

### Sprint 2 — v1.1.0 (2026-05-09)
**Ключевые итоги:** Инфраструктура автодоставки. APScheduler с SQLAlchemy JobStore, `deliver_reminders` job (interval=1 мин), `morning_digest`, `watchdog` (interval=10 мин). 21 unit-тест введён.

**Артефакты:** `stage4-dev/outputs/DEV-*-sprint2*`, `stage5-testing/outputs/`

---

### Sprint 3 — v1.2.0 (2026-05-10)
**Ключевые итоги:** 5 новых Stories (19 SP). Удаление заметок (`/delnote`), история выполненных задач (`/donetasks`), административная сводка (`/adminoverview`), напоминание о задаче (`/taskremind`), назначение задачи с подтверждением (`/taskassign` + inline callback Accept/Decline). Миграция Alembic 0002. 43/43 unit-тестов.

**Вердикт QA:** CONDITIONAL GO — UAT в живом Telegram ожидает проведения.

**Артефакты:**
- `tracking/sprints/sprint-03.md` — финальный отчёт план vs факт
- `stage1-planning/outputs/PM-2026-05-10-sprint3.md`
- `stage4-dev/outputs/DEV-2026-05-10-sprint3-summary.md`
- `stage4-dev/outputs/DEV-2026-05-10-code-review-sprint3.md`
- `stage5-testing/outputs/QA-2026-05-10-go-no-go-sprint3.md`
- `stage5-testing/outputs/AUTO-2026-05-10-coverage-sprint3.md`
- `stage6-deploy/outputs/REL-2026-05-10-release-notes-v1.2.0.md`

---

## Velocity по спринтам

| Sprint | Плановый SP | Фактический SP | Отклонение |
|--------|-------------|----------------|------------|
| Sprint 1 | 20 | 20 | 0% |
| Sprint 2 | — | — | N/A (инфра) |
| Sprint 3 | 20 | 19 | -1 SP (резерв, плановое) |

**Средний velocity (Sprint 1 + 3):** 19–20 SP на спринт при 1 разработчике.

---

## Накопленный технический долг

| ID | Описание | Приоритет | Целевой Sprint |
|----|----------|-----------|----------------|
| TD-01 | Ellipsis sentinel → `_UNSET` в task_repo.py | Medium | Sprint 4 |
| TD-02 | `_parse_scheduled_at()` → app/utils/date_parser.py | Medium | Sprint 4 |
| TD-03 | AuthMiddleware: username TTL | Low | Sprint 4 |
| TD-04 | Интеграционные тесты с реальной PostgreSQL | Medium | Sprint 4 |
| TD-05 | CI/CD pipeline | High | Sprint 4 |
