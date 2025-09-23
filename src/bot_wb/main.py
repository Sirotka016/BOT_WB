import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from .settings import settings
from .logger import logger
from .storage.db import ensure_db
from .handlers.start import router as start_router
from .handlers.auth import router as auth_router


async def setup_commands(bot: Bot):
    await bot.set_my_commands([BotCommand(command="start", description="Start")])


async def main():
    await ensure_db()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_routers(start_router, auth_router)

    await setup_commands(bot)
    logger.info("BOT_WB started")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
