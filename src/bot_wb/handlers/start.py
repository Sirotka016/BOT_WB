from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ._render import render_home

router = Router(name=__name__)


@router.message(CommandStart())
async def on_start(message: Message):
    user_name = message.from_user.full_name if message.from_user else "друг"
    await render_home(message.bot, message.chat.id, user_name)
