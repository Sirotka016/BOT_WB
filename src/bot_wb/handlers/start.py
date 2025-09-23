from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..ui.keyboards import kb_home
from ..ui.texts import home_text

router = Router(name=__name__)


@router.message(CommandStart())
async def on_start(message: Message):
    user_name = message.from_user.full_name if message.from_user else "друг"
    await message.answer(home_text(user_name), reply_markup=kb_home())
