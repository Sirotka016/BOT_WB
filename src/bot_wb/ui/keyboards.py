from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


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


def kb_auth_stub() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ]
        ]
    )


def kb_logout() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Выйти из аккаунта", callback_data="logout")],
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ],
        ]
    )
