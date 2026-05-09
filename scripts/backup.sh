#!/usr/bin/env bash
# =============================================================================
# backup.sh — Скрипт резервного копирования FamilyPlannerBot
# =============================================================================
#
# Назначение:
#   Создаёт дамп PostgreSQL через docker exec, сохраняет в ./backups/,
#   удаляет файлы старше 30 дней (ротация).
#
# Использование:
#   ./scripts/backup.sh
#
# Переменные окружения (читаются из .env рядом со скриптом):
#   DB_NAME     — имя базы данных (по умолчанию: familybot)
#   DB_USER     — пользователь PostgreSQL (по умолчанию: familybot)
#   DB_CONTAINER — имя контейнера БД (по умолчанию: fpb_db)
#
# Настройка автоматического запуска через cron:
# ------------------------------------------------------------
#   Откройте редактор crontab:
#     crontab -e
#
#   Добавьте строку для запуска каждый день в 03:00:
#     0 3 * * * /absolute/path/to/FamilyPlannerBot/scripts/backup.sh >> /absolute/path/to/FamilyPlannerBot/backups/cron.log 2>&1
#
#   Пример (замените путь на реальный):
#     0 3 * * * /home/user/FamilyPlannerBot/scripts/backup.sh >> /home/user/FamilyPlannerBot/backups/cron.log 2>&1
#
# Проверить список cron-задач:
#   crontab -l
# =============================================================================

set -euo pipefail

# --- Конфигурация -----------------------------------------------------------

# Определяем корень проекта относительно расположения скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Загружаем переменные из .env если файл существует
ENV_FILE="${PROJECT_DIR}/.env"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$ENV_FILE"
    set +a
fi

# Параметры с fallback-значениями
DB_NAME="${DB_NAME:-familybot}"
DB_USER="${DB_USER:-familybot}"
DB_CONTAINER="${DB_CONTAINER:-fpb_db}"

# Директория для бэкапов (NFR-SEC-06: права 700)
BACKUP_DIR="${PROJECT_DIR}/backups"

# Срок хранения бэкапов (дни)
RETENTION_DAYS=30

# Имя файла с меткой времени
TIMESTAMP="$(date +%Y-%m-%d_%H-%M)"
BACKUP_FILE="${BACKUP_DIR}/${TIMESTAMP}.sql.gz"

# --- Функции -----------------------------------------------------------------

log_info() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] [INFO]  $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] [ERROR] $*" >&2
}

# --- Подготовка директории --------------------------------------------------

# Создать директорию бэкапов если не существует
if [[ ! -d "$BACKUP_DIR" ]]; then
    mkdir -p "$BACKUP_DIR"
    log_info "Создана директория бэкапов: $BACKUP_DIR"
fi

# Установить права 700 (только владелец) — NFR-SEC-06
chmod 700 "$BACKUP_DIR"

# --- Проверка контейнера ----------------------------------------------------

if ! docker inspect "$DB_CONTAINER" > /dev/null 2>&1; then
    log_error "Контейнер '$DB_CONTAINER' не найден. Убедитесь что docker compose up -d выполнен."
    exit 1
fi

CONTAINER_STATUS="$(docker inspect -f '{{.State.Status}}' "$DB_CONTAINER")"
if [[ "$CONTAINER_STATUS" != "running" ]]; then
    log_error "Контейнер '$DB_CONTAINER' не запущен (статус: $CONTAINER_STATUS)."
    exit 1
fi

# --- Создание дампа ---------------------------------------------------------

log_info "Начало резервного копирования базы '$DB_NAME' из контейнера '$DB_CONTAINER'..."

START_TIME="$(date +%s)"

if docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    END_TIME="$(date +%s)"
    DURATION=$(( END_TIME - START_TIME ))
    FILE_SIZE="$(du -sh "$BACKUP_FILE" 2>/dev/null | cut -f1)"
    log_info "Бэкап успешно создан: $BACKUP_FILE (размер: $FILE_SIZE, время: ${DURATION}с)"
else
    log_error "Ошибка при создании бэкапа! Файл: $BACKUP_FILE"
    # Удалить неполный файл
    rm -f "$BACKUP_FILE"
    exit 1
fi

# --- Ротация старых бэкапов -------------------------------------------------

log_info "Удаление бэкапов старше ${RETENTION_DAYS} дней..."

DELETED_COUNT=0
while IFS= read -r -d '' old_file; do
    rm -f "$old_file"
    log_info "Удалён старый бэкап: $old_file"
    (( DELETED_COUNT++ )) || true
done < <(find "$BACKUP_DIR" -maxdepth 1 -name "*.sql.gz" -mtime "+${RETENTION_DAYS}" -print0)

if [[ $DELETED_COUNT -gt 0 ]]; then
    log_info "Удалено файлов: $DELETED_COUNT"
else
    log_info "Файлов для удаления не найдено (ротация не требуется)."
fi

# --- Итог -------------------------------------------------------------------

TOTAL_BACKUPS="$(find "$BACKUP_DIR" -maxdepth 1 -name "*.sql.gz" | wc -l | tr -d ' ')"
log_info "Резервное копирование завершено. Всего бэкапов: $TOTAL_BACKUPS"
