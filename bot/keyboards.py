from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📨 Подать заявку", callback_data="apply")],
    ])


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="confirm_edit"),
        ],
    ])


def edit_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆔 ID",           callback_data="edit_field:id")],
        [InlineKeyboardButton(text="🎮 Ник",          callback_data="edit_field:nickname")],
        [InlineKeyboardButton(text="🏆 Competitive",  callback_data="edit_field:rank_comp")],
        [InlineKeyboardButton(text="🤝 Allies",       callback_data="edit_field:rank_allies")],
        [InlineKeyboardButton(text="⚔️ Duels",        callback_data="edit_field:rank_duels")],
        [InlineKeyboardButton(text="⏱ Часы",          callback_data="edit_field:hours")],
        [InlineKeyboardButton(text="📊 KD",           callback_data="edit_field:kd")],
    ])


def admin_kb(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять",      callback_data=f"admin_accept:{app_id}"),
            InlineKeyboardButton(text="❌ Отклонить",     callback_data=f"admin_reject:{app_id}"),
        ],
        [
            InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"admin_block:{app_id}"),
        ],
    ])
