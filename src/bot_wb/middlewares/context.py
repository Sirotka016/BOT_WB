from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot_wb.logging import logger, pop_log_context, push_log_context

Handler = Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]]


class ContextMiddleware(BaseMiddleware):
    """Middleware that enriches log context with telegram identifiers."""

    async def __call__(
        self,
        handler: Handler,
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        chat = data.get("event_chat")
        handler_name = getattr(handler, "__qualname__", handler.__class__.__name__)
        token = push_log_context(
            tg_id=getattr(user, "id", None),
            chat_id=getattr(chat, "id", None),
            handler=handler_name,
        )
        logger.debug("Handling event {}", event.__class__.__name__)
        try:
            return await handler(event, data)
        finally:
            pop_log_context(token)
