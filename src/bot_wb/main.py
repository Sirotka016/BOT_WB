import asyncio
import socket
import time
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramConflictError, TelegramNetworkError
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

PORT_LOCK = 58112
CONFLICT_DIAG_WINDOW = 10.0


def _acquire_port_lock() -> socket.socket | None:
    socket_guard = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        socket_guard.bind(("127.0.0.1", PORT_LOCK))
        socket_guard.listen(1)
        return socket_guard
    except OSError:
        socket_guard.close()
        return None


def _acquire_file_lock(lock: FileLock, lock_path: Path) -> bool:
    try:
        lock.acquire(timeout=0)
        return True
    except Timeout:
        logger.error("Another BOT_WB instance is already running (lock: %s). Exit.", lock_path)
        return False


def _setup_middlewares(dp: Dispatcher) -> None:
    context_mw = ContextMiddleware()
    error_mw = ErrorMiddleware()
    for router in (dp.message, dp.callback_query, dp.my_chat_member, dp.chat_member):
        router.middleware(context_mw)
        router.middleware(error_mw)


def _build_app() -> tuple[Bot, Dispatcher]:
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_routers(start_router, auth_router, profile_router)
    _setup_middlewares(dp)
    return bot, dp


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands([BotCommand(command="start", description="Start")])


async def _close_bot(bot: Bot) -> None:
    with suppress(Exception):
        await bot.session.close()


async def _start_polling_with_retries(dp: Dispatcher, bot: Bot) -> None:
    start_ts = time.monotonic()
    retries = 0
    while True:
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            return
        except TelegramConflictError as error:
            retries += 1
            if time.monotonic() - start_ts > CONFLICT_DIAG_WINDOW:
                logger.error(
                    "409 Conflict persists. Token is used elsewhere. "
                    "Use /revoke in BotFather. Details: %s",
                    error,
                )
                return
            logger.warning("409 Conflict received: %s. Retrying...", error)
            await asyncio.sleep(min(2.0 + retries * 0.5, 5.0))
        except TelegramNetworkError as error:
            retries += 1
            logger.warning("Network error: %s — retrying...", error)
            await asyncio.sleep(min(2.0 + retries * 0.5, 5.0))


async def _run_bot(bot: Bot, dp: Dispatcher) -> None:
    data_dir = Path(getattr(settings, "data_dir", "data"))
    lock_path = data_dir / "bot_wb.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock = FileLock(str(lock_path))

    if not _acquire_file_lock(lock, lock_path):
        await _close_bot(bot)
        return

    port_guard: socket.socket | None = None
    try:
        port_guard = _acquire_port_lock()
        if not port_guard:
            logger.error("Port lock %s is busy. Another local instance is running.", PORT_LOCK)
            return

        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.warning(
                "Webhook is set to %s — deleting before long polling...",
                webhook_info.url,
            )
            await bot.delete_webhook(drop_pending_updates=True)

        logger.info("BOT_WB started")
        await _start_polling_with_retries(dp, bot)
    finally:
        await _close_bot(bot)
        with suppress(Exception):
            if port_guard:
                port_guard.close()
        with suppress(Exception):
            lock.release()
        logger.info("BOT_WB shutdown complete")


async def main() -> None:
    setup_logging(settings.log_level)
    logger.info("Bootstrapping BOT_WB")
    await ensure_db()

    bot, dp = _build_app()

    await setup_commands(bot)
    await _run_bot(bot, dp)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped by signal")
