#!/usr/bin/env bash
# =============================================================================
# restore.sh — Скрипт восстановления FamilyPlannerBot из резервной копии
# =============================================================================
#
# Назначение:
#   Восстанавливает базу данных PostgreSQL из дампа .sql.gz.
#   Перед восстановлением останавливает бота, после — запускает обратно
#   и проверяет что контейнер поднялся.
#
# Использование:
#   ./scripts/restore.sh <путь_к_файлу_бэкапа>
#
# Пример:
#   ./scripts/restore.sh ./backups/2026-05-09_03-00.sql.gz
#   ./scripts/restore.sh /home/user/FamilyPlannerBot/backups/2026-05-09_03-00.sql.gz
#
# ВНИМАНИЕ:
#   - Все текущие данные в базе будут ЗАМЕНЕНЫ данными из бэкапа
#   - Операция необратима без отдельного бэкапа текущего состояния
#
# Переменные окружения (читаются из .env):
#   DB_NAME       — имя базы данных
#   DB_USER       — пользователь PostgreSQL
#   DB_CONTAINER  — имя контейнера БД (по умолчанию: fpb_db)
#   BOT_CONTAINER — имя контейнера бота (по умолчанию: fpb_bot)
# =============================================================================

set -euo pipefail

# --- Функции -----------------------------------------------------------------

log_info() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] [INFO]  $*"
}

log_error() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] [ERROR] $*" >&2
}

log_warn() {
    echo "[$(date '+%Y-%m-%dT%H:%M:%S')] [WARN]  $*"
}

# --- Проверка аргументов ----------------------------------------------------

if [[ $# -lt 1 ]]; then
    log_error "Не указан файл бэкапа."
    echo ""
    echo "Использование: $0 <путь_к_файлу_бэкапа>"
    echo "Пример:        $0 ./backups/2026-05-09_03-00.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    log_error "Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

# --- Конфигурация -----------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

ENV_FILE="${PROJECT_DIR}/.env"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$ENV_FILE"
    set +a
fi

DB_NAME="${DB_NAME:-familybot}"
DB_USER="${DB_USER:-familybot}"
DB_CONTAINER="${DB_CONTAINER:-fpb_db}"
BOT_CONTAINER="${BOT_CONTAINER:-fpb_bot}"

# Максимальное ожидание запуска бота (секунды)
BOT_START_TIMEOUT=60

# --- Предупреждение пользователю --------------------------------------------

log_warn "================================================="
log_warn "ВНИМАНИЕ: Восстановление из бэкапа"
log_warn "Файл: $BACKUP_FILE"
log_warn "База: $DB_NAME"
log_warn "ВСЕ ТЕКУЩИЕ ДАННЫЕ БУДУТ ЗАМЕНЕНЫ!"
log_warn "================================================="
echo ""
read -r -p "Продолжить? Введите 'yes' для подтверждения: " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    log_info "Операция отменена пользователем."
    exit 0
fi

# --- Проверка контейнеров ---------------------------------------------------

log_info "Проверка статуса контейнеров..."

if ! docker inspect "$DB_CONTAINER" > /dev/null 2>&1; then
    log_error "Контейнер БД '$DB_CONTAINER' не найден. Запустите: docker compose up -d db"
    exit 1
fi

DB_STATUS="$(docker inspect -f '{{.State.Status}}' "$DB_CONTAINER")"
if [[ "$DB_STATUS" != "running" ]]; then
    log_error "Контейнер БД '$DB_CONTAINER' не запущен (статус: $DB_STATUS)."
    exit 1
fi

log_info "Контейнер БД '$DB_CONTAINER' работает."

# --- Остановка бота ---------------------------------------------------------

BOT_WAS_RUNNING=false

if docker inspect "$BOT_CONTAINER" > /dev/null 2>&1; then
    BOT_STATUS="$(docker inspect -f '{{.State.Status}}' "$BOT_CONTAINER")"
    if [[ "$BOT_STATUS" == "running" ]]; then
        log_info "Останавливаем бота '$BOT_CONTAINER'..."
        cd "$PROJECT_DIR"
        docker compose stop bot
        BOT_WAS_RUNNING=true
        log_info "Бот остановлен."
    else
        log_info "Бот '$BOT_CONTAINER' уже не запущен (статус: $BOT_STATUS)."
    fi
else
    log_warn "Контейнер бота '$BOT_CONTAINER' не найден — продолжаем без остановки."
fi

# --- Восстановление базы данных ---------------------------------------------

log_info "Начало восстановления базы '$DB_NAME' из файла: $BACKUP_FILE"

START_TIME="$(date +%s)"

# Сбрасываем существующие соединения и пересоздаём БД
log_info "Сброс существующих соединений к БД..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

log_info "Удаление и пересоздание базы данных..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS ${DB_NAME};" \
    > /dev/null

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d postgres \
    -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" \
    > /dev/null

log_info "Восстановление данных из дампа..."
if gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null; then
    END_TIME="$(date +%s)"
    DURATION=$(( END_TIME - START_TIME ))
    log_info "База данных успешно восстановлена (время: ${DURATION}с)."
else
    log_error "Ошибка при восстановлении базы данных!"
    log_error "База '$DB_NAME' может быть в неконсистентном состоянии."
    log_error "Рекомендуется: запустите restore.sh повторно с рабочим бэкапом."
    exit 1
fi

# --- Запуск бота ------------------------------------------------------------

if [[ "$BOT_WAS_RUNNING" == "true" ]]; then
    log_info "Запускаем бота '$BOT_CONTAINER'..."
    cd "$PROJECT_DIR"
    docker compose start bot

    # Проверка что бот поднялся
    log_info "Ожидание запуска бота (таймаут: ${BOT_START_TIMEOUT}с)..."
    ELAPSED=0
    while [[ $ELAPSED -lt $BOT_START_TIMEOUT ]]; do
        CURRENT_STATUS="$(docker inspect -f '{{.State.Status}}' "$BOT_CONTAINER" 2>/dev/null || echo 'unknown')"
        if [[ "$CURRENT_STATUS" == "running" ]]; then
            log_info "Бот '$BOT_CONTAINER' успешно запущен (статус: running)."
            break
        fi
        sleep 2
        (( ELAPSED += 2 )) || true
    done

    if [[ $ELAPSED -ge $BOT_START_TIMEOUT ]]; then
        log_warn "Бот не запустился за ${BOT_START_TIMEOUT}с. Проверьте вручную:"
        log_warn "  docker compose ps"
        log_warn "  docker compose logs -f bot"
    fi
else
    log_info "Бот не был запущен до восстановления — не запускаем автоматически."
    log_info "Для запуска выполните: docker compose up -d"
fi

# --- Итог -------------------------------------------------------------------

log_info "================================================="
log_info "Восстановление завершено."
log_info "Файл бэкапа: $BACKUP_FILE"
log_info "База данных: $DB_NAME"
log_info ""
log_info "Для проверки работоспособности бота:"
log_info "  docker compose ps"
log_info "  docker compose logs -f bot"
log_info "  Напишите /start в Telegram"
log_info "================================================="
