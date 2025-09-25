from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from ._render import render_home

router = Router(name=__name__)


@router.message(CommandStart())
async def on_start(message: Message):
    user_name = message.from_user.full_name if message.from_user else "друг"
    await render_home(message.bot, message.chat.id, user_name)


@router.callback_query(F.data == "home")
async def on_home(callback: CallbackQuery):
    user_name = callback.from_user.full_name if callback.from_user else "друг"
    await render_home(callback.bot, callback.message.chat.id, user_name)
    await callback.answer()


@router.callback_query(F.data == "refresh")
async def on_refresh(callback: CallbackQuery):
    user_name = callback.from_user.full_name if callback.from_user else "друг"
    await render_home(callback.bot, callback.message.chat.id, user_name, force_replace=True)
    await callback.answer("Обновлено")
