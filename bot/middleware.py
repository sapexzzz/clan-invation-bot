from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from bot.database import is_user_blocked

BLOCKED_TEXT = "🚫 Вы заблокированы. Доступ к боту ограничен."


class BlockMiddleware(BaseMiddleware):
    """Отклоняет любые апдейты от заблокированных пользователей."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Достаём user_id из апдейта
        user_id: int | None = None

        if isinstance(event, Update):
            if event.message:
                user_id = event.message.from_user.id if event.message.from_user else None
            elif event.callback_query:
                user_id = event.callback_query.from_user.id

        if user_id and await is_user_blocked(user_id):
            # Уведомляем один раз и обрываем цепочку обработчиков
            if isinstance(event, Update):
                if event.message:
                    await event.message.answer(BLOCKED_TEXT)
                elif event.callback_query:
                    await event.callback_query.answer(BLOCKED_TEXT, show_alert=True)
            return  # не передаём дальше

        return await handler(event, data)
