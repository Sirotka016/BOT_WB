from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from bot_wb.logging import logger
from bot_wb.services.auth_service import AuthService
from bot_wb.storage.repo import UserRepo
from bot_wb.ui.keyboards import kb_home
from bot_wb.ui.texts import home_text

_repo = UserRepo()
_auth = AuthService(_repo)


async def _safe_edit(bot: Bot, chat_id: int, message_id: int, text: str, markup):
    try:
        await bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=markup,
        )
        logger.debug("Edited anchor message {} for chat {}", message_id, chat_id)
        return True
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            logger.debug("Ignored not-modified edit for chat {}", chat_id)
            return False
        raise


async def _replace_message(bot: Bot, chat_id: int, text: str, markup):
    anchor = await _repo.get_anchor(chat_id)
    if anchor:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=anchor)
        except TelegramBadRequest as exc:
            logger.debug(
                "Cannot delete anchor message {} in chat {}: {}",
                anchor,
                chat_id,
                exc,
            )
    msg = await bot.send_message(chat_id, text, reply_markup=markup)
    await _repo.set_anchor(chat_id, msg.message_id)
    logger.debug("Replaced anchor message in chat {} -> {}", chat_id, msg.message_id)
    return msg.message_id


async def _edit_or_send(bot: Bot, chat_id: int, text: str, markup):
    anchor = await _repo.get_anchor(chat_id)
    if anchor:
        ok = await _safe_edit(bot, chat_id, anchor, text, markup)
        if ok:
            return anchor
    msg = await bot.send_message(chat_id, text, reply_markup=markup)
    await _repo.set_anchor(chat_id, msg.message_id)
    logger.debug("Created anchor message in chat {} -> {}", chat_id, msg.message_id)
    return msg.message_id


async def render_home(
    bot: Bot,
    chat_id: int,
    user_name: str,
    force_replace: bool = False,
) -> None:
    authorized = await _auth.is_authorized(chat_id)
    text = home_text(user_name, authorized)
    markup = kb_home(authorized=authorized)
    if force_replace:
        await _replace_message(bot, chat_id, text, markup)
    else:
        await _edit_or_send(bot, chat_id, text, markup)
    await _repo.set_view(chat_id, "home")
    logger.info("Rendered home view for chat {}", chat_id)
