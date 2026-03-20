import time

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.database import get_last_application_time, get_pending_application
from bot.keyboards import start_kb
from bot.states import ApplicationStates

ANTISPAM_SECONDS = 600  # 10 минут

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "👋 Привет!\n\n"
        "Ты можешь подать заявку в клан.\n\n"
        "❗ Важно:\n"
        "- Указывай реальные данные\n"
        "- Минимальные требования:\n"
        "  • KD >= 1.0\n"
        "  • Часы >= 50\n\n"
        "Нажми кнопку ниже, чтобы начать ⬇️",
        reply_markup=start_kb(),
    )


@router.callback_query(F.data == "apply")
async def on_apply(callback: CallbackQuery, state: FSMContext) -> None:
    user_id = callback.from_user.id

    # Анти-спам
    last_time = await get_last_application_time(user_id)
    if last_time is not None and (time.time() - last_time) < ANTISPAM_SECONDS:
        await callback.answer(
            "⛔ Подожди перед повторной заявкой (10 минут)",
            show_alert=True,
        )
        return

    # Блок pending
    pending = await get_pending_application(user_id)
    if pending:
        await callback.answer(
            "⏳ У тебя уже есть заявка на рассмотрении. Дождись ответа.",
            show_alert=True,
        )
        return

    await callback.answer()
    await state.set_state(ApplicationStates.waiting_for_id)
    await callback.message.answer("📌 Введи свой ID:")
