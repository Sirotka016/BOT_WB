from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from ..settings import settings


def kb_home(authorized: bool) -> InlineKeyboardMarkup:
    row1 = []
    if authorized:
        row1.append(
            InlineKeyboardButton(
                text="👤 Профиль",
                web_app=WebAppInfo(url=f"{settings.webapp_public_url}/app/profile"),
            )
        )
    else:
        row1.append(InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth"))
    row1.append(InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            row1,
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )


def kb_auth_stub() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ]
        ]
    )


def kb_profile() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Выйти из аккаунта", callback_data="logout")],
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ],
        ]
    )
