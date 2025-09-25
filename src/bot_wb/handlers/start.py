from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from ._render import render_home

router = Router(name=__name__)


@router.message(CommandStart())
async def on_start(message: Message):
    user_name = message.from_user.full_name if message.from_user else "друг"
    if message.bot is None or message.chat is None:
        raise RuntimeError("Message does not contain bot or chat context")
    await render_home(message.bot, message.chat.id, user_name)


@router.callback_query(F.data == "home")
async def on_home(callback: CallbackQuery):
    user_name = callback.from_user.full_name if callback.from_user else "друг"
    if callback.bot is None or callback.message is None or callback.message.chat is None:
        raise RuntimeError("Callback does not contain required context")
    await render_home(callback.bot, callback.message.chat.id, user_name)
    await callback.answer()


@router.callback_query(F.data == "refresh")
async def on_refresh(callback: CallbackQuery):
    user_name = callback.from_user.full_name if callback.from_user else "друг"
    if callback.bot is None or callback.message is None or callback.message.chat is None:
        raise RuntimeError("Callback does not contain required context")
    await render_home(
        callback.bot,
        callback.message.chat.id,
        user_name,
        force_replace=True,
    )
    await callback.answer("Обновлено")
