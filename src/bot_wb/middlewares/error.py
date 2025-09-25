from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot_wb.logging import logger

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class ErrorMiddleware(BaseMiddleware):
    """Middleware that logs exceptions and notifies the user."""

    async def __call__(
        self,
        handler: Handler,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:  # noqa: BLE001
            logger.opt(exception=True).error("Unhandled exception in handler")
            await self._notify(event)
            return None

    async def _notify(self, event: TelegramObject) -> None:
        message_text = "⚠️ Произошла ошибка. Попробуйте выполнить действие ещё раз позже."
        if isinstance(event, CallbackQuery):
            if event.message:
                await event.message.answer(message_text)
            with suppress_telegram_error():
                await event.answer("Произошла ошибка", show_alert=True)
        elif isinstance(event, Message):
            with suppress_telegram_error():
                await event.answer(message_text)


class suppress_telegram_error:
    def __enter__(self) -> None:  # noqa: D401 - simple context manager
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        if isinstance(exc, TelegramBadRequest):
            logger.debug(
                "Ignoring TelegramBadRequest during error notification: {}",
                exc,
            )
            return True
        return False
