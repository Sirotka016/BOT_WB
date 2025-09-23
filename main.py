import asyncio
import os
from dataclasses import dataclass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
)
from dotenv import load_dotenv
from loguru import logger

# ---------------------- settings ----------------------
load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")


settings = Settings()
if not settings.bot_token:
    raise RuntimeError("BOT_TOKEN is empty. Put it into .env")


# ---------------------- ui helpers ----------------------
def kb_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh"),
            ],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )


def kb_auth() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ]
        ]
    )


def home_text(user_name: str) -> str:
    # Текст приветствия по ТЗ
    return (
        f"Привет, {user_name}.\n"
        f"Я бот поставок Football Shop 🤖!\n"
        f"На WB я умею бронировать поставки, искать слоты и перераспределять товары.\n"
        f"А так же создавать поставки с вашим товаром за вас!"
    )


def auth_stub_text() -> str:
    # Текст заглушки авторизации — как на скрине
    return (
        "❌ Телефон не заполнен\n"
        "❌ Авторизация не пройдена\n"
        "____________________________\n"
        "Для продолжения нужно отправить номер телефона в формате +79181234567, "
        "который используется для входа на портал WB Партнеры"
    )


# ---------------------- bot init ----------------------
bot = Bot(token=settings.bot_token)
dp = Dispatcher()


# ---------------------- commands & handlers ----------------------
@dp.message(CommandStart())
async def on_start(message: Message):
    """
    Показываем стартовое 'окно' с тремя кнопками.
    """
    user_name = message.from_user.full_name if message.from_user else "друг"
    await message.answer(home_text(user_name), reply_markup=kb_home())


@dp.callback_query(F.data == "refresh")
async def on_refresh(cb: CallbackQuery):
    """
    'Обновить' — перерисовываем это же окно (одно окно, без новых сообщений).
    """
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    try:
        await cb.message.edit_text(home_text(user_name), reply_markup=kb_home())
    except Exception as e:
        logger.warning(f"edit_text failed on refresh: {e}")
        # fallback: если предыдущее сообщение нельзя редактировать, отвечаем новым
        await cb.message.answer(home_text(user_name), reply_markup=kb_home())
    await cb.answer()


@dp.callback_query(F.data == "auth")
async def on_auth(cb: CallbackQuery):
    """
    Открываем 'окно' авторизации (заглушка) — строго в том же сообщении.
    """
    try:
        await cb.message.edit_text(auth_stub_text(), reply_markup=kb_auth())
    except Exception as e:
        logger.warning(f"edit_text failed on auth: {e}")
        await cb.message.answer(auth_stub_text(), reply_markup=kb_auth())
    await cb.answer()


@dp.callback_query(F.data == "home")
async def on_home(cb: CallbackQuery):
    """
    Кнопка 'Домой' со страницы авторизации — возврат на экран приветствия.
    """
    user_name = cb.from_user.full_name if cb.from_user else "друг"
    try:
        await cb.message.edit_text(home_text(user_name), reply_markup=kb_home())
    except Exception as e:
        logger.warning(f"edit_text failed on home: {e}")
        await cb.message.answer(home_text(user_name), reply_markup=kb_home())
    await cb.answer()


@dp.callback_query(F.data == "close")
async def on_close(cb: CallbackQuery):
    """
    Полное закрытие окна: заменяем текущий текст и убираем клавиатуру.
    """
    try:
        await cb.message.edit_text(
            "Сессия завершена. Нажмите /start для новой сессии.", reply_markup=None
        )
    except Exception as e:
        logger.warning(f"edit_text failed on close: {e}")
        await cb.message.answer("Сессия завершена. Нажмите /start для новой сессии.")
    await cb.answer()


async def setup_commands():
    await bot.set_my_commands([BotCommand(command="start", description="Start")])


async def main():
    logger.info("Starting BOT_WB…")
    await setup_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped.")
