"""Handlers для команд /start и /help."""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

logger = logging.getLogger(__name__)

router = Router(name="start")

HELP_TEXT = """
👨‍👩‍👧‍👦 *Семейный планировщик* — ваш личный ассистент для всей семьи.

*Задачи:*
/tasks — список активных задач
/addtask Купить хлеб — добавить задачу
/donetask 5 — отметить задачу выполненной
/deltask 5 — удалить задачу

*Заметки:*
/notes — список заметок
/addnote Рецепт борща: ... — добавить заметку

*Напоминания:*
/reminders — мои напоминания
/addreminder 2026-05-10 14:30 Позвонить врачу — создать напоминание
/delreminder 3 — удалить напоминание

*Календарь:*
/calendar — ближайшие события
/addevent 2026-05-15 День рождения Маши — добавить событие

*Прочее:*
/start — приветствие
/help — эта справка

_Дата: ГГГГ-ММ-ДД, Время: ЧЧ:ММ (московское время)_
""".strip()

WELCOME_TEXT = (
    "Привет, {name}! 👋\n\n"
    "Я — семейный планировщик. Помогу вам держать дела под контролем: "
    "задачи, заметки, напоминания и общий календарь.\n\n"
    "Введите /help, чтобы увидеть все команды."
)


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Приветствие при первом запуске или повторном /start."""
    if message.from_user is None:
        return
    name = message.from_user.first_name or "Пользователь"
    logger.info("user=%d action=start", message.from_user.id)
    await message.answer(WELCOME_TEXT.format(name=name))


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    """Список всех команд бота (≤30 строк, NFR-USAB-01)."""
    if message.from_user is None:
        return
    logger.info("user=%d action=help", message.from_user.id)
    await message.answer(HELP_TEXT, parse_mode="Markdown")
