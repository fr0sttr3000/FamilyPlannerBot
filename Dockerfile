# Dockerfile — образ FamilyPlannerBot
# Базовый образ: python:3.11-slim (минимальный footprint)
FROM python:3.11-slim

# Метаданные
LABEL org.opencontainers.image.title="FamilyPlannerBot"
LABEL org.opencontainers.image.description="Telegram-бот семейного планирования"

# Рабочая директория
WORKDIR /app

# Системные зависимости для psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements для кэширования слоёв Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# Директория для бэкапов (монтируется как volume)
RUN mkdir -p /app/backups

# НЕ запускаем от root (безопасность)
RUN useradd --no-create-home --shell /bin/false botuser
USER botuser

# Точка входа
CMD ["python", "-m", "app.main"]

# Запуск: docker compose up -d
# Логи: docker compose logs -f bot
