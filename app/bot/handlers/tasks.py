"""Handlers для управления задачами.

Команды: /tasks, /addtask, /donetask, /deltask
"""
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="tasks")

TASKS_EMPTY = "Активных задач нет. Добавьте первую: /addtask Купить хлеб"
ADDTASK_USAGE = "Укажите текст задачи. Пример: /addtask Купить хлеб"
DONETASK_USAGE = "Укажите ID задачи. Пример: /donetask 5"
DELTASK_USAGE = "Укажите ID задачи. Пример: /deltask 5"


def _format_task_list(tasks: list) -> str:
    """Форматирует список задач для вывода."""
    lines = ["📋 *Активные задачи:*\n"]
    for task in tasks:
        creator = task.creator.first_name if task.creator else "Неизвестно"
        date_str = task.created_at.strftime("%d.%m")
        lines.append(f"• [{task.id}] {task.text} _{creator}, {date_str}_")
    return "\n".join(lines)


@router.message(Command("tasks"))
async def tasks_handler(message: Message, session: AsyncSession) -> None:
    """Показать список активных задач семьи."""
    if message.from_user is None:
        return
    try:
        service = TaskService(session)
        tasks = await service.get_active_tasks()
        if not tasks:
            await message.answer(TASKS_EMPTY)
            return
        await message.answer(_format_task_list(tasks), parse_mode="Markdown")
        logger.info("user=%d action=tasks_list count=%d", message.from_user.id, len(tasks))
    except Exception:
        logger.exception("Ошибка в /tasks user=%d", message.from_user.id)
        await message.answer("Не удалось загрузить задачи. Попробуйте позже.")


@router.message(Command("addtask"))
async def addtask_handler(message: Message, session: AsyncSession) -> None:
    """Добавить новую задачу."""
    if message.from_user is None:
        return
    text = (message.text or "").removeprefix("/addtask").strip()
    if not text:
        await message.answer(ADDTASK_USAGE)
        return
    try:
        service = TaskService(session)
        result = await service.create_task(message.from_user.id, text)
        if result.success and result.task:
            await message.answer(
                f"✅ Задача добавлена: {result.task.text} (ID: {result.task.id})"
            )
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /addtask user=%d", message.from_user.id)
        await message.answer("Не удалось добавить задачу. Попробуйте позже.")


@router.message(Command("donetask"))
async def donetask_handler(message: Message, session: AsyncSession) -> None:
    """Отметить задачу выполненной."""
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/donetask").strip()
    if not args.isdigit():
        await message.answer(DONETASK_USAGE)
        return
    try:
        service = TaskService(session)
        result = await service.complete_task(int(args), message.from_user.id)
        if result.success and result.task:
            await message.answer(f"✅ Задача {result.task.id} выполнена!")
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /donetask user=%d", message.from_user.id)
        await message.answer("Не удалось отметить задачу. Попробуйте позже.")


@router.message(Command("deltask"))
async def deltask_handler(message: Message, session: AsyncSession) -> None:
    """Удалить задачу (soft delete)."""
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/deltask").strip()
    if not args.isdigit():
        await message.answer(DELTASK_USAGE)
        return
    try:
        service = TaskService(session)
        result = await service.delete_task(int(args), message.from_user.id)
        if result.success:
            await message.answer(f"🗑 Задача {args} удалена.")
        else:
            await message.answer(f"❌ {result.error}")
    except Exception:
        logger.exception("Ошибка в /deltask user=%d", message.from_user.id)
        await message.answer("Не удалось удалить задачу. Попробуйте позже.")
