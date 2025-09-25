import asyncio
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from filelock import FileLock, Timeout

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

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_routers(start_router, auth_router, profile_router)
    _setup_middlewares(dp)

    await setup_commands(bot)

    lock_path = Path(getattr(settings, "data_dir", Path("data"))) / "bot_wb.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path))

    try:
        lock.acquire(timeout=0)
    except Timeout:
        logger.error(
            "Another BOT_WB instance is already running (lock: %s). Exit.",
            lock_path,
        )
        with suppress(Exception):
            await bot.session.close()
        return

    try:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.warning(
                "Webhook is set to %s — deleting before long polling...",
                webhook_info.url,
            )
            await bot.delete_webhook(drop_pending_updates=True)

        logger.info("BOT_WB started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        with suppress(Exception):
            await bot.session.close()
        with suppress(Exception):
            lock.release()
        logger.info("BOT_WB shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped by signal")
