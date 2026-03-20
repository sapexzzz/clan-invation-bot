from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot import config
from bot.database import (
    create_application,
    update_application_status,
    upsert_user_timestamp,
)
from bot.keyboards import admin_kb, confirm_kb, edit_menu_kb
from bot.states import ApplicationStates

router = Router()

# Порядок полей для навигации при последовательном вводе
FIELD_ORDER = [
    "id",
    "nickname",
    "rank_comp",
    "rank_allies",
    "rank_duels",
    "hours",
    "kd",
]

FIELD_PROMPTS: dict[str, str] = {
    "id":          "📌 Введи свой ID:",
    "nickname":    "🎮 Введи свой ник:",
    "rank_comp":   "🏆 Звание в соревновательном режиме:",
    "rank_allies": "🤝 Звание в режиме Напарники:",
    "rank_duels":  "⚔️ Звание в режиме Дуэли:",
    "hours":       "⏱ Сколько часов на аккаунте?",
    "kd":          "📊 Укажи KD (например 1.25):",
}

FIELD_STATE_MAP: dict[str, str] = {
    "id":          ApplicationStates.waiting_for_id,
    "nickname":    ApplicationStates.waiting_for_nickname,
    "rank_comp":   ApplicationStates.waiting_for_rank_comp,
    "rank_allies": ApplicationStates.waiting_for_rank_allies,
    "rank_duels":  ApplicationStates.waiting_for_rank_duels,
    "hours":       ApplicationStates.waiting_for_hours,
    "kd":          ApplicationStates.waiting_for_kd,
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_summary(data: dict) -> str:
    return (
        "📋 Проверь данные:\n\n"
        f"🎮 Ник: {data.get('nickname', '—')}\n"
        f"🆔 ID: {data.get('game_id', '—')}\n\n"
        "🏆 Ранги:\n"
        f"  - Competitive: {data.get('rank_comp', '—')}\n"
        f"  - Allies: {data.get('rank_allies', '—')}\n"
        f"  - Duels: {data.get('rank_duels', '—')}\n\n"
        f"⏱ Часы: {data.get('hours', '—')}\n"
        f"📊 KD: {data.get('kd', '—')}\n\n"
        "Отправить заявку?"
    )


def _build_group_text(user: dict, data: dict) -> str:
    username_str = f"@{user['username']}" if user.get("username") else f"tg://user?id={user['id']}"
    return (
        "🚨 Новая заявка\n\n"
        f"👤 {username_str}\n"
        f"🆔 TG ID: {user['id']}\n\n"
        f"🎮 Ник: {data['nickname']}\n"
        f"🆔 Игровой ID: {data['game_id']}\n\n"
        "🏆 Ранги:\n"
        f"  - Competitive: {data['rank_comp']}\n"
        f"  - Allies: {data['rank_allies']}\n"
        f"  - Duels: {data['rank_duels']}\n\n"
        f"⏱ Часы: {data['hours']}\n"
        f"📊 KD: {data['kd']}"
    )


async def _go_to_next_step(
    state: FSMContext,
    message: Message,
    current_field: str,
) -> None:
    """После ввода поля: если редактирование — возвращаем на confirm, иначе следующий шаг."""
    data = await state.get_data()
    if data.get("editing"):
        await state.update_data(editing=False)
        await state.set_state(ApplicationStates.confirm)
        await message.answer(_build_summary(data), reply_markup=confirm_kb())
        return

    idx = FIELD_ORDER.index(current_field)
    if idx + 1 < len(FIELD_ORDER):
        next_field = FIELD_ORDER[idx + 1]
        await state.set_state(FIELD_STATE_MAP[next_field])
        await message.answer(FIELD_PROMPTS[next_field])
    else:
        # Дошли до конца — показываем подтверждение
        await state.set_state(ApplicationStates.confirm)
        await message.answer(_build_summary(data), reply_markup=confirm_kb())


# ─── FSM steps ────────────────────────────────────────────────────────────────

@router.message(ApplicationStates.waiting_for_id)
async def step_id(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    if not text.isdigit():
        await message.answer("❗ ID должен содержать только цифры. Попробуй ещё раз:")
        return
    await state.update_data(game_id=text)
    await _go_to_next_step(state, message, "id")


@router.message(ApplicationStates.waiting_for_nickname)
async def step_nickname(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("❗ Ник не может быть пустым. Попробуй ещё раз:")
        return
    await state.update_data(nickname=text)
    await _go_to_next_step(state, message, "nickname")


@router.message(ApplicationStates.waiting_for_rank_comp)
async def step_rank_comp(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("❗ Введи звание. Попробуй ещё раз:")
        return
    await state.update_data(rank_comp=text)
    await _go_to_next_step(state, message, "rank_comp")


@router.message(ApplicationStates.waiting_for_rank_allies)
async def step_rank_allies(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("❗ Введи звание. Попробуй ещё раз:")
        return
    await state.update_data(rank_allies=text)
    await _go_to_next_step(state, message, "rank_allies")


@router.message(ApplicationStates.waiting_for_rank_duels)
async def step_rank_duels(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("❗ Введи звание. Попробуй ещё раз:")
        return
    await state.update_data(rank_duels=text)
    await _go_to_next_step(state, message, "rank_duels")


@router.message(ApplicationStates.waiting_for_hours)
async def step_hours(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer("❗ Введи целое число часов. Попробуй ещё раз:")
        return
    hours = int(text)
    if hours < 50:
        # Авто-отклонение
        data = await state.get_data()
        await create_application(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            nickname=data.get("nickname", ""),
            game_id=data.get("game_id", ""),
            rank_comp=data.get("rank_comp", ""),
            rank_allies=data.get("rank_allies", ""),
            rank_duels=data.get("rank_duels", ""),
            hours=hours,
            kd=0.0,
            status="rejected_auto",
        )
        await upsert_user_timestamp(message.from_user.id)
        await state.clear()
        await message.answer(
            "❌ Заявка автоматически отклонена.\n\n"
            "Минимальные требования:\n"
            "- KD >= 1.0\n"
            "- Часы >= 50"
        )
        return
    await state.update_data(hours=hours)
    await _go_to_next_step(state, message, "hours")


@router.message(ApplicationStates.waiting_for_kd)
async def step_kd(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().replace(",", ".")
    try:
        kd = float(text)
    except ValueError:
        await message.answer("❗ KD должен быть числом (например 1.25). Попробуй ещё раз:")
        return

    if kd < 1.0 or kd > 10.0:
        # Авто-отклонение
        data = await state.get_data()
        await create_application(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            nickname=data.get("nickname", ""),
            game_id=data.get("game_id", ""),
            rank_comp=data.get("rank_comp", ""),
            rank_allies=data.get("rank_allies", ""),
            rank_duels=data.get("rank_duels", ""),
            hours=data.get("hours", 0),
            kd=kd,
            status="rejected_auto",
        )
        await upsert_user_timestamp(message.from_user.id)
        await state.clear()
        await message.answer(
            "❌ Заявка автоматически отклонена.\n\n"
            "Минимальные требования:\n"
            "- KD >= 1.0\n"
            "- Часы >= 50"
        )
        return

    await state.update_data(kd=kd)
    await _go_to_next_step(state, message, "kd")


# ─── Confirm ──────────────────────────────────────────────────────────────────

@router.callback_query(ApplicationStates.confirm, F.data == "confirm_yes")
async def on_confirm_yes(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()

    user = callback.from_user

    # Сохранить в БД (без group_message_id пока)
    app_id = await create_application(
        telegram_id=user.id,
        username=user.username,
        nickname=data["nickname"],
        game_id=data["game_id"],
        rank_comp=data["rank_comp"],
        rank_allies=data["rank_allies"],
        rank_duels=data["rank_duels"],
        hours=data["hours"],
        kd=data["kd"],
        status="pending",
    )
    await upsert_user_timestamp(user.id)

    # Отправить в группу
    group_text = _build_group_text(
        {"id": user.id, "username": user.username},
        data,
    )
    send_kwargs: dict = {
        "chat_id": config.GROUP_ID,
        "text": group_text,
        "reply_markup": admin_kb(app_id),
    }
    if config.TOPIC_ID:
        send_kwargs["message_thread_id"] = config.TOPIC_ID

    group_msg = await bot.send_message(**send_kwargs)

    # Сохранить group_message_id
    await update_application_status(app_id, "pending", group_message_id=group_msg.message_id)

    await callback.answer()
    await callback.message.edit_text("📨 Заявка отправлена!")


@router.callback_query(ApplicationStates.confirm, F.data == "confirm_edit")
async def on_confirm_edit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(ApplicationStates.edit_field_choice)
    await callback.message.answer(
        "✏️ Какое поле хочешь изменить?",
        reply_markup=edit_menu_kb(),
    )


# ─── Edit field choice ────────────────────────────────────────────────────────

@router.callback_query(ApplicationStates.edit_field_choice, F.data.startswith("edit_field:"))
async def on_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    field = callback.data.split(":")[1]
    if field not in FIELD_STATE_MAP:
        await callback.answer("Неизвестное поле", show_alert=True)
        return

    await callback.answer()
    await state.update_data(editing=True)
    await state.set_state(FIELD_STATE_MAP[field])
    await callback.message.answer(FIELD_PROMPTS[field])
