from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from ..services.auth_service import AuthService
from ..storage.repo import UserRepo
from ..ui.keyboards import kb_home
from ..ui.texts import home_text

repo = UserRepo()
_auth = AuthService(repo)


async def render_home(bot: Bot, chat_id: int, user_name: str):
    authorized = await _auth.is_authorized(chat_id)
    text = home_text(user_name, authorized)
    markup: InlineKeyboardMarkup = kb_home(authorized)
    await _edit_anchor(bot, chat_id, text, markup)
    await repo.set_view(chat_id, "home")


async def _edit_anchor(bot: Bot, chat_id: int, text: str, markup: InlineKeyboardMarkup | None):
    anchor = await repo.get_anchor(chat_id)
    if anchor:
        try:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=anchor,
                reply_markup=markup,
            )
            return
        except Exception:
            pass
    msg = await bot.send_message(chat_id, text, reply_markup=markup)
    await repo.set_anchor(chat_id, msg.message_id)
