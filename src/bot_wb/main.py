import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .handlers.auth import router as auth_router
from .handlers.profile import router as profile_router
from .handlers.start import router as start_router
from .logging import logger, setup_logging
from .middlewares.context import ContextMiddleware
from .middlewares.error import ErrorMiddleware
from .settings import settings
from .storage.db import ensure_db


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands([BotCommand(command="start", description="Start")])


def _setup_middlewares(dp: Dispatcher) -> None:
    context_mw = ContextMiddleware()
    error_mw = ErrorMiddleware()
    for router in (dp.message, dp.callback_query, dp.my_chat_member, dp.chat_member):
        router.middleware(context_mw)
        router.middleware(error_mw)


async def main() -> None:
    setup_logging(settings.log_level)
    logger.info("Bootstrapping BOT_WB")
    await ensure_db()

    dp = Dispatcher()
    dp.include_routers(start_router, auth_router, profile_router)
    _setup_middlewares(dp)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await setup_commands(bot)
    logger.info("BOT_WB started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        with suppress(Exception):
            await bot.session.close()
        logger.info("BOT_WB shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped by signal")
