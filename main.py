import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot import config
from bot.database import init_db
from bot.handlers import admin, application, start


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    await init_db()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок важен: admin должен быть до application,
    # чтобы admin_accept/admin_reject не перехватывались FSM-фильтрами
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(application.router)

    logging.info("Бот запущен")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
