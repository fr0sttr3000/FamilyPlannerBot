# INSTALL-GUIDE.md — FamilyPlannerBot

**Аудитория:** Установщик / системный администратор  
**Уровень:** Базовые навыки командной строки  
**Время прохождения:** 15–30 минут  
**Дата:** 2026-05-09

---

## Содержание

1. [Предварительные требования](#1-предварительные-требования)
2. [Получение Bot Token через @BotFather](#2-получение-bot-token-через-botfather)
3. [Загрузка проекта](#3-загрузка-проекта)
4. [Заполнение конфигурации .env](#4-заполнение-конфигурации-env)
5. [Запуск бота](#5-запуск-бота)
6. [Проверка работоспособности](#6-проверка-работоспособности)
7. [Настройка автоматического бэкапа](#7-настройка-автоматического-бэкапа)
8. [Переезд на новый хост](#8-переезд-на-новый-хост)
9. [Обновление бота до новой версии](#9-обновление-бота-до-новой-версии)
10. [Остановка и удаление](#10-остановка-и-удаление)

---

## 1. Предварительные требования

### Поддерживаемые операционные системы

| ОС | Версия | Статус |
|---|---|---|
| Linux (Ubuntu) | 22.04 LTS и новее | Рекомендуется |
| Linux (Debian) | 11 (Bullseye) и новее | Поддерживается |
| macOS | 13 (Ventura) и новее | Поддерживается |
| Windows | 10/11 с WSL2 | Поддерживается |

> **Windows:** Все команды ниже выполняются в терминале WSL2 (Ubuntu). Установка WSL2: [docs.microsoft.com/windows/wsl/install](https://docs.microsoft.com/windows/wsl/install)

### Необходимое программное обеспечение

**Docker Engine** (версия 24.0 или новее):

```bash
# Проверить версию
docker --version
# Ожидаемый вывод: Docker version 24.x.x, build ...
```

Установка Docker: [docs.docker.com/engine/install](https://docs.docker.com/engine/install/)

**Docker Compose** (версия 2.20 или новее):

```bash
# Проверить версию
docker compose version
# Ожидаемый вывод: Docker Compose version v2.x.x
```

> Docker Desktop для macOS и Windows включает Docker Compose автоматически.

### Доступ к интернету

Для работы бота необходим исходящий HTTPS-доступ к `api.telegram.org` (порт 443). Если вы используете корпоративный прокси или firewall — убедитесь что этот адрес разрешён.

---

## 2. Получение Bot Token через @BotFather

Bot Token — это уникальный ключ вашего бота. Без него бот не запустится.

**Шаг 1.** Откройте Telegram и найдите бота `@BotFather` (официальный бот Telegram).

**Шаг 2.** Отправьте команду:
```
/newbot
```

**Шаг 3.** BotFather спросит имя бота (отображаемое имя, например `Family Planner`). Введите имя.

**Шаг 4.** BotFather спросит username бота (должен заканчиваться на `bot`, например `myfamily_plannerbot`). Введите username.

**Шаг 5.** BotFather выдаст токен вида:
```
1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
```

**Сохраните этот токен** — он понадобится на следующем шаге. Никому не передавайте токен; любой, кто его знает, может управлять вашим ботом.

**Шаг 6 (необязательно).** Настройте описание бота:
```
/setdescription → выберите бота → введите описание
```

---

## 3. Загрузка проекта

### Вариант A: Клонирование через Git

```bash
git clone https://github.com/YOUR_USERNAME/FamilyPlannerBot.git
cd FamilyPlannerBot
```

### Вариант B: Скачивание архива

```bash
# Скачайте ZIP-архив через браузер или wget:
wget https://github.com/YOUR_USERNAME/FamilyPlannerBot/archive/refs/heads/main.zip
unzip main.zip
cd FamilyPlannerBot-main
```

После загрузки убедитесь что структура директорий корректна:

```bash
ls
# Ожидаемый вывод: Dockerfile  docker-compose.yml  .env.example  app/  ...
```

---

## 4. Заполнение конфигурации .env

Все настройки бота хранятся в файле `.env`. Никогда не коммитьте этот файл в git.

**Шаг 1.** Создайте файл `.env` из шаблона:

```bash
cp .env.example .env
```

**Шаг 2.** Откройте файл в текстовом редакторе:

```bash
nano .env
# или: vi .env
# или: code .env  (если установлен VS Code)
```

**Шаг 3.** Заполните все переменные по таблице ниже:

| Переменная | Описание | Пример |
|---|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather | `1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw` |
| `OWNER_ID` | Ваш Telegram ID (числовой) | `123456789` |
| `DB_HOST` | Имя сервиса БД в Docker Compose | `db` (не менять) |
| `DB_PORT` | Порт PostgreSQL | `5432` (не менять) |
| `DB_NAME` | Имя базы данных | `familybot` |
| `DB_USER` | Пользователь PostgreSQL | `familybot` |
| `DB_PASSWORD` | Пароль PostgreSQL | придумайте надёжный пароль |
| `ALLOWED_USERS` | Telegram ID членов семьи через запятую | `123456789,987654321` |
| `TIMEZONE` | Часовой пояс | `Europe/Moscow` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `APP_VERSION` | Версия образа (не :latest) | `v1.0.0` |

**Как узнать свой Telegram ID:**
1. Откройте Telegram
2. Найдите бота `@userinfobot`
3. Отправьте `/start` — бот ответит вашим ID

**Пример заполненного .env:**
```dotenv
BOT_TOKEN=1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
OWNER_ID=123456789
DB_HOST=db
DB_PORT=5432
DB_NAME=familybot
DB_USER=familybot
DB_PASSWORD=MyStr0ngP@ssword!
ALLOWED_USERS=123456789,987654321,555000111
TIMEZONE=Europe/Moscow
LOG_LEVEL=INFO
APP_VERSION=v1.0.0
```

**Шаг 4.** Сохраните файл (в nano: `Ctrl+O`, `Enter`, `Ctrl+X`).

**Шаг 5.** Проверьте права доступа к файлу:
```bash
chmod 600 .env
ls -la .env
# Ожидаемый вывод: -rw------- 1 user user ... .env
```

---

## 5. Запуск бота

```bash
docker compose up -d
```

При первом запуске Docker:
1. Скачает образ `postgres:15-alpine` (~90 МБ)
2. Соберёт образ бота (установит Python-зависимости)
3. Запустит контейнеры `fpb_db` и `fpb_bot`
4. Бот автоматически применит миграции базы данных

Первый запуск занимает 2–5 минут. Последующие — секунды.

---

## 6. Проверка работоспособности

### Проверка 1: Статус контейнеров

```bash
docker compose ps
```

Ожидаемый вывод:
```
NAME      IMAGE                        STATUS          PORTS
fpb_bot   familyplannerbot:v1.0.0      Up 2 minutes
fpb_db    postgres:15-alpine           Up 2 minutes (healthy)
```

Оба контейнера должны быть `Up`. Статус `fpb_db` должен быть `(healthy)`.

### Проверка 2: Логи бота

```bash
docker compose logs -f bot
```

В логах должно быть сообщение об успешном запуске. Для выхода нажмите `Ctrl+C`.

Если видите ошибки `BOT_TOKEN not found` или `Connection refused` — проверьте файл `.env`.

### Проверка 3: Telegram

Откройте Telegram и найдите вашего бота по username. Отправьте:
```
/start
```

Бот должен ответить приветственным сообщением в течение 3 секунд.

### Что делать если бот не отвечает

```bash
# Посмотреть последние 50 строк логов
docker compose logs --tail=50 bot

# Проверить состояние healthcheck базы данных
docker inspect fpb_db | grep -A 10 '"Health"'

# Перезапустить только бота (без перезапуска БД)
docker compose restart bot
```

---

## 7. Настройка автоматического бэкапа

Бэкап создаётся скриптом `scripts/backup.sh`. Рекомендуется настроить запуск каждую ночь.

**Шаг 1.** Убедитесь что скрипт исполняемый:

```bash
chmod +x scripts/backup.sh
```

**Шаг 2.** Проверьте что скрипт работает вручную:

```bash
./scripts/backup.sh
# Ожидаемый вывод: [INFO] Бэкап успешно создан: ./backups/2026-05-09_03-00.sql.gz
```

**Шаг 3.** Откройте редактор crontab:

```bash
crontab -e
```

**Шаг 4.** Добавьте строку (замените `/absolute/path` на реальный путь к проекту):

```
0 3 * * * /absolute/path/FamilyPlannerBot/scripts/backup.sh >> /absolute/path/FamilyPlannerBot/backups/cron.log 2>&1
```

Пример с реальным путём:
```
0 3 * * * /home/ubuntu/FamilyPlannerBot/scripts/backup.sh >> /home/ubuntu/FamilyPlannerBot/backups/cron.log 2>&1
```

Это означает: запускать каждый день в 03:00.

**Шаг 5.** Сохраните и проверьте:

```bash
crontab -l
# Должны увидеть добавленную строку
```

Бэкапы сохраняются в `./backups/` и хранятся 30 дней. Старые файлы удаляются автоматически.

---

## 8. Переезд на новый хост

Используйте этот раздел при переносе бота на другой компьютер или VPS.

### На старом хосте: создание бэкапа

```bash
cd /путь/к/FamilyPlannerBot

# Создать бэкап базы данных
./scripts/backup.sh

# Убедиться что бэкап создан
ls -lh backups/
```

### Перенос файлов на новый хост

```bash
# Скопировать бэкап и файл .env на новый хост
scp backups/ПОСЛЕДНИЙ_ФАЙЛ.sql.gz user@new-host:/tmp/
scp .env user@new-host:/tmp/
```

### На новом хосте: установка

```bash
# 1. Клонировать/скачать проект (см. раздел 3)
git clone https://github.com/YOUR_USERNAME/FamilyPlannerBot.git
cd FamilyPlannerBot

# 2. Восстановить .env
cp /tmp/.env .env

# 3. Запустить только базу данных
docker compose up -d db

# 4. Дождаться готовности БД (20-30 секунд)
docker compose ps
# fpb_db должен быть Up (healthy)

# 5. Восстановить данные из бэкапа
./scripts/restore.sh /tmp/ПОСЛЕДНИЙ_ФАЙЛ.sql.gz

# 6. Запустить бота
docker compose up -d bot
```

### Проверка после миграции

```bash
docker compose ps
docker compose logs -f bot
# Написать /start в Telegram
```

---

## 9. Обновление бота до новой версии

```bash
cd /путь/к/FamilyPlannerBot

# 1. Получить новую версию кода
git pull

# 2. Обновить значение APP_VERSION в .env
#    Например: APP_VERSION=v1.1.0
nano .env

# 3. Пересобрать и перезапустить
docker compose build bot
docker compose up -d bot

# 4. Проверить что бот запустился
docker compose ps
docker compose logs --tail=20 bot
```

Миграции базы данных применяются автоматически при старте бота.

Время недоступности при обновлении: 10–60 секунд.

---

## 10. Остановка и удаление

### Остановить бота (данные сохраняются)

```bash
docker compose down
```

### Запустить снова

```bash
docker compose up -d
```

### Полное удаление (с данными)

```bash
# ВНИМАНИЕ: Удаляет все данные бота без возможности восстановления
# Предварительно сделайте бэкап: ./scripts/backup.sh

docker compose down --volumes
docker rmi familyplannerbot:v1.0.0
```

---

## Краткая памятка команд

```bash
# Запуск
docker compose up -d

# Статус
docker compose ps

# Логи (в реальном времени)
docker compose logs -f bot

# Перезапуск только бота
docker compose restart bot

# Остановка (данные сохраняются)
docker compose down

# Ручной бэкап
./scripts/backup.sh

# Восстановление из бэкапа
./scripts/restore.sh ./backups/2026-05-09_03-00.sql.gz
```
