"""Handlers для управления задачами.

Команды: /tasks, /addtask, /donetask, /deltask,
         /donetasks, /taskremind, /taskassign
Callbacks: assign_accept:*, assign_decline:*
"""
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import ASSIGNMENT_STATUS_ACCEPTED, ASSIGNMENT_STATUS_PENDING
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = Router(name="tasks")

# Сообщения
TASKS_EMPTY = "Активных задач нет. Добавьте первую: /addtask Купить хлеб"
DONETASKS_EMPTY = "За последние 30 дней задачи не выполнялись."
ADDTASK_USAGE = "Укажите текст задачи. Пример: /addtask Купить хлеб"
DONETASK_USAGE = "Укажите ID задачи. Пример: /donetask 5"
DELTASK_USAGE = "Укажите ID задачи. Пример: /deltask 5"
TASKREMIND_USAGE = "Укажите ID задачи, дату и время. Пример: /taskremind 3 2026-06-01 10:00"
TASKASSIGN_USAGE = "Укажите ID задачи и @username. Пример: /taskassign 5 @masha"


def _build_assignment_keyboard(task_id: int, assigner_id: int) -> InlineKeyboardMarkup:
    """Сформировать inline-клавиатуру для подтверждения назначения задачи."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Принять",
            callback_data=f"assign_accept:{task_id}:{assigner_id}",
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"assign_decline:{task_id}:{assigner_id}",
        ),
    ]])


def _format_task_list(tasks: list) -> str:
    """Форматирует список активных задач с индикатором назначения (US-33)."""
    lines = ["📋 <b>Активные задачи:</b>\n"]
    for task in tasks:
        creator = task.creator.first_name if task.creator else "Неизвестно"
        date_str = task.created_at.strftime("%d.%m")

        # Индикатор назначения
        assignment_suffix = ""
        if task.assignment_status == ASSIGNMENT_STATUS_PENDING and task.assignee:
            assignee_name = (
                f"@{task.assignee.username}"
                if task.assignee.username
                else task.assignee.first_name
            )
            assignment_suffix = f" <i>[ожидает {assignee_name}]</i>"
        elif task.assignment_status == ASSIGNMENT_STATUS_ACCEPTED and task.assignee:
            assignee_name = (
                f"@{task.assignee.username}"
                if task.assignee.username
                else task.assignee.first_name
            )
            assignment_suffix = f" <i>[принята {assignee_name}]</i>"

        lines.append(f"• [{task.id}] {task.text} <i>{creator}, {date_str}</i>{assignment_suffix}")
    return "\n".join(lines)


def _format_completed_tasks(tasks: list) -> str:
    """Форматирует историю выполненных задач (US-13)."""
    lines = ["✅ <b>Выполненные задачи (последние 30 дней):</b>\n"]
    for task in tasks:
        completer = task.completer.first_name if task.completer else "Неизвестно"
        date_str = task.completed_at.strftime("%d.%m.%Y %H:%M") if task.completed_at else "—"
        lines.append(f"• [{task.id}] {task.text} — <i>{completer}, {date_str}</i>")
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
        await message.answer(_format_task_list(tasks), parse_mode="HTML")
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


@router.message(Command("donetasks"))
async def donetasks_handler(message: Message, session: AsyncSession) -> None:
    """Показать историю выполненных задач за последние 30 дней (US-13)."""
    if message.from_user is None:
        return
    try:
        service = TaskService(session)
        tasks = await service.get_completed_tasks()
        if not tasks:
            await message.answer(DONETASKS_EMPTY)
            return
        await message.answer(_format_completed_tasks(tasks), parse_mode="HTML")
        logger.info("user=%d action=donetasks count=%d", message.from_user.id, len(tasks))
    except Exception:
        logger.exception("Ошибка в /donetasks user=%d", message.from_user.id)
        await message.answer("Не удалось загрузить историю задач. Попробуйте позже.")


@router.message(Command("taskremind"))
async def taskremind_handler(message: Message, session: AsyncSession) -> None:
    """Создать напоминание о задаче (US-32).

    Формат: /taskremind <ID> <YYYY-MM-DD> <HH:MM>
    """
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/taskremind").strip().split()
    if len(args) < 3 or not args[0].isdigit():
        await message.answer(TASKREMIND_USAGE)
        return
    task_id = int(args[0])
    date_str = args[1]
    time_str = args[2]
    try:
        service = TaskService(session)
        result = await service.create_task_reminder(
            task_id=task_id,
            user_id=message.from_user.id,
            date_str=date_str,
            time_str=time_str,
        )
        if result.success and result.task:
            await message.answer(
                f"⏰ Напоминание о задаче #{task_id} установлено на {date_str} {time_str}.\n"
                f"Если задача будет выполнена раньше — напоминание будет пропущено."
            )
        else:
            await message.answer(f"❌ {result.error}")
        logger.info(
            "user=%d action=taskremind task_id=%d success=%s",
            message.from_user.id, task_id, result.success,
        )
    except Exception:
        logger.exception("Ошибка в /taskremind user=%d task_id=%d", message.from_user.id, task_id)
        await message.answer("Не удалось создать напоминание. Попробуйте позже.")


@router.message(Command("taskassign"))
async def taskassign_handler(message: Message, session: AsyncSession, bot: Bot) -> None:
    """Назначить задачу другому члену семьи (US-33).

    Формат: /taskassign <ID> @username
    """
    if message.from_user is None:
        return
    args = (message.text or "").removeprefix("/taskassign").strip().split(maxsplit=1)
    if len(args) < 2 or not args[0].isdigit():
        await message.answer(TASKASSIGN_USAGE)
        return
    task_id = int(args[0])
    target_username = args[1].strip()
    try:
        service = TaskService(session)
        result = await service.assign_task(
            task_id=task_id,
            assigner_user_id=message.from_user.id,
            target_username=target_username,
        )
        if not result.success:
            await message.answer(f"❌ {result.error}")
            return

        # Уведомить адресата с inline-клавиатурой
        assigner_name = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else message.from_user.first_name
        )
        keyboard = _build_assignment_keyboard(task_id, message.from_user.id)
        notification_text = (
            f"📋 {assigner_name} назначил(а) вам задачу #{task_id}:\n"
            f"«{result.task.text}»\n\n"
            f"Принять или отклонить?"
        )
        try:
            await bot.send_message(
                result.target_user_id,
                notification_text,
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception(
                "taskassign: не удалось уведомить assignee=%d task_id=%d",
                result.target_user_id, task_id,
            )

        clean_username = target_username.lstrip("@")
        await message.answer(
            f"✅ Задача #{task_id} назначена @{clean_username}. Ожидаем подтверждения."
        )
        logger.info(
            "user=%d action=taskassign task_id=%d assignee=%d",
            message.from_user.id, task_id, result.target_user_id,
        )
    except Exception:
        logger.exception("Ошибка в /taskassign user=%d task_id=%d", message.from_user.id, task_id)
        await message.answer("Не удалось назначить задачу. Попробуйте позже.")


async def _process_assignment_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    bot: Bot,
    *,
    accepted: bool,
) -> None:
    """Общая логика обработки Accept/Decline с защитой от race condition."""
    if callback.from_user is None or callback.data is None or callback.message is None:
        await callback.answer()
        return

    # Разобрать callback_data: "assign_accept:{task_id}:{assigner_id}"
    try:
        _, task_id_str, assigner_id_str = callback.data.split(":")
        task_id = int(task_id_str)
        assigner_id = int(assigner_id_str)
    except (ValueError, AttributeError):
        await callback.answer("Некорректные данные кнопки.", show_alert=True)
        return

    service = TaskService(session)

    # Защита от race condition: перечитать task из БД и проверить актуальный статус
    task = await service.get_task_by_id(task_id)
    if task is None:
        await callback.answer("Задача не найдена.", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    if task.assignment_status != ASSIGNMENT_STATUS_PENDING:
        await callback.answer("Ответ уже был получен ранее.", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=None)
        return

    # Проверить что отвечает именно тот пользователь, которому назначена задача
    if task.assigned_to != callback.from_user.id:
        await callback.answer("Эта задача назначена другому пользователю.", show_alert=True)
        return

    # Применить решение
    responder_name = (
        f"@{callback.from_user.username}"
        if callback.from_user.username
        else callback.from_user.first_name
    )

    if accepted:
        await service.accept_assignment(task_id)
        assigner_message = f"✅ {responder_name} принял(а) задачу #{task_id}."
        assignee_reply = f"✅ Вы приняли задачу #{task_id}."
    else:
        await service.decline_assignment(task_id)
        assigner_message = (
            f"❌ {responder_name} отклонил(а) задачу #{task_id}. "
            f"Задача возвращена в общий пул."
        )
        assignee_reply = f"❌ Вы отклонили задачу #{task_id}."

    # Инвалидировать кнопки у адресата
    await callback.message.edit_reply_markup(reply_markup=None)

    # Уведомить адресата
    await callback.answer(assignee_reply, show_alert=False)

    # Уведомить создателя задачи через инъектированный bot (aiogram 3.x)
    try:
        await bot.send_message(assigner_id, assigner_message)
    except Exception:
        logger.warning(
            "callback_assign: не удалось уведомить assigner_id=%d task_id=%d",
            assigner_id, task_id,
        )

    logger.info(
        "user=%d action=task_assign_response task_id=%d accepted=%s",
        callback.from_user.id, task_id, accepted,
    )


@router.callback_query(F.data.startswith("assign_accept:"))
async def cb_assign_accept(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Пользователь принял назначенную задачу (US-33)."""
    try:
        await _process_assignment_callback(callback, session, bot, accepted=True)
    except Exception:
        uid = callback.from_user.id if callback.from_user else 0
        logger.exception("Ошибка в callback assign_accept user=%d", uid)
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)


@router.callback_query(F.data.startswith("assign_decline:"))
async def cb_assign_decline(callback: CallbackQuery, session: AsyncSession, bot: Bot) -> None:
    """Пользователь отклонил назначенную задачу (US-33)."""
    try:
        await _process_assignment_callback(callback, session, bot, accepted=False)
    except Exception:
        uid = callback.from_user.id if callback.from_user else 0
        logger.exception("Ошибка в callback assign_decline user=%d", uid)
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)
