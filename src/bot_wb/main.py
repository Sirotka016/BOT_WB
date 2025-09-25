import asyncio
from contextlib import suppress

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from .handlers.auth import router as auth_router
from .handlers.profile import router as profile_router
from .handlers.start import router as start_router
from .logger import logger
from .settings import settings
from .storage.db import ensure_db
from .webapp_server import app as webapp


async def setup_commands(bot: Bot):
    await bot.set_my_commands([BotCommand(command="start", description="Start")])


async def run_webapp():
    config = uvicorn.Config(
        webapp,
        host=settings.webapp_host,
        port=settings.webapp_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    await ensure_db()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_routers(start_router, auth_router, profile_router)

    await setup_commands(bot)
    logger.info("BOT_WB started")
    bot_task = asyncio.create_task(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    )
    web_task = asyncio.create_task(run_webapp())
    _, pending = await asyncio.wait(
        {bot_task, web_task}, return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped")
