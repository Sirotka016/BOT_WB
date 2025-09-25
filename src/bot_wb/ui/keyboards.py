from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def kb_home(authorized: bool) -> InlineKeyboardMarkup:
    primary_button = (
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
        if authorized
        else InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth")
    )
    rows = [
        [primary_button],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_auth_stub() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ],
        ],
    )


def kb_profile_view(has_multiple: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_multiple:
        rows.append(
            [
                InlineKeyboardButton(
                    text="🔀 Сменить профиль",
                    callback_data="profile_switch",
                ),
            ],
        )
    rows.append(
        [
            InlineKeyboardButton(text="🚪 Выйти с аккаунта", callback_data="logout"),
        ],
    )
    rows.append(
        [
            InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="profile_refresh"),
        ],
    )
    rows.append(
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_profile_switch(
    profiles: list[tuple[str, str]],
    active_id: str | None,
) -> InlineKeyboardMarkup:
    keyboard: list[list[InlineKeyboardButton]] = []
    for pid, name in profiles:
        label = f"✅ {name}" if pid == active_id else name
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"set_profile:{pid}",
                ),
            ],
        )
    keyboard.append(
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="profile"),
            InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
        ],
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
