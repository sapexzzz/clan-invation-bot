from datetime import datetime, timedelta, timezone

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery

from bot import config
from bot.database import get_application_by_id, update_application_status, block_user

router = Router()

ADMIN_ROLES = ("administrator", "creator")


async def _check_admin(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=config.GROUP_ID, user_id=user_id)
        return member.status in ADMIN_ROLES
    except Exception:
        return False


# ─── Accept ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_accept:"))
async def on_admin_accept(callback: CallbackQuery, bot: Bot) -> None:
    if not await _check_admin(bot, callback.from_user.id):
        await callback.answer("⛔ Нет прав", show_alert=True)
        return

    app_id = int(callback.data.split(":")[1])
    app = await get_application_by_id(app_id)

    if not app:
        await callback.answer("❗ Заявка не найдена", show_alert=True)
        return

    if app["status"] != "pending":
        await callback.answer("ℹ️ Заявка уже обработана", show_alert=True)
        return

    # Создать invite link (24 часа, 1 использование)
    expire_dt = datetime.now(tz=timezone.utc) + timedelta(hours=24)
    try:
        invite = await bot.create_chat_invite_link(
            chat_id=config.GROUP_ID,
            expire_date=expire_dt,
            member_limit=1,
        )
        invite_link = invite.invite_link
    except Exception as e:
        await callback.answer(f"❗ Не удалось создать ссылку: {e}", show_alert=True)
        return

    await update_application_status(app_id, "accepted")

    # Уведомить пользователя
    try:
        await bot.send_message(
            chat_id=app["telegram_id"],
            text=(
                "✅ Заявка принята!\n\n"
                f"Вот ссылка (24 часа):\n{invite_link}"
            ),
        )
    except Exception:
        pass  # Пользователь мог заблокировать бота

    # Обновить сообщение в группе
    admin_name = callback.from_user.username
    admin_str = f"@{admin_name}" if admin_name else callback.from_user.full_name
    await callback.answer()
    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Принято — {admin_str}",
        reply_markup=None,
    )


# ─── Reject ───────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_reject:"))
async def on_admin_reject(callback: CallbackQuery, bot: Bot) -> None:
    if not await _check_admin(bot, callback.from_user.id):
        await callback.answer("⛔ Нет прав", show_alert=True)
        return

    app_id = int(callback.data.split(":")[1])
    app = await get_application_by_id(app_id)

    if not app:
        await callback.answer("❗ Заявка не найдена", show_alert=True)
        return

    if app["status"] != "pending":
        await callback.answer("ℹ️ Заявка уже обработана", show_alert=True)
        return

    await update_application_status(app_id, "rejected")

    # Уведомить пользователя
    try:
        await bot.send_message(
            chat_id=app["telegram_id"],
            text="❌ Заявка отклонена",
        )
    except Exception:
        pass

    # Обновить сообщение в группе
    admin_name = callback.from_user.username
    admin_str = f"@{admin_name}" if admin_name else callback.from_user.full_name
    await callback.answer()
    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ Отклонено — {admin_str}",
        reply_markup=None,
    )


# ─── Block ────────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_block:"))
async def on_admin_block(callback: CallbackQuery, bot: Bot) -> None:
    if not await _check_admin(bot, callback.from_user.id):
        await callback.answer("⛔ Нет прав", show_alert=True)
        return

    app_id = int(callback.data.split(":")[1])
    app = await get_application_by_id(app_id)

    if not app:
        await callback.answer("❗ Заявка не найдена", show_alert=True)
        return

    if app["status"] != "pending":
        await callback.answer("ℹ️ Заявка уже обработана", show_alert=True)
        return

    await block_user(app["telegram_id"])
    await update_application_status(app_id, "rejected")

    # Уведомить пользователя
    try:
        await bot.send_message(
            chat_id=app["telegram_id"],
            text="🚫 Ты заблокирован. Подача заявок недоступна.",
        )
    except Exception:
        pass

    admin_name = callback.from_user.username
    admin_str = f"@{admin_name}" if admin_name else callback.from_user.full_name
    await callback.answer("🚫 Пользователь заблокирован")
    await callback.message.edit_text(
        callback.message.text + f"\n\n🚫 Заблокирован — {admin_str}",
        reply_markup=None,
    )
