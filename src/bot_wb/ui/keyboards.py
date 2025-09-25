from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def kb_home(authorized: bool) -> InlineKeyboardMarkup:
    row1 = []
    if authorized:
        row1.append(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    else:
        row1.append(InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth"))
    row2 = [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")]
    row3 = [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2, row3])


def kb_auth_stub() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
                InlineKeyboardButton(text="❌ Закрыть", callback_data="close"),
            ]
        ]
    )


def kb_profile_view(has_multiple: bool) -> InlineKeyboardMarkup:
    rows = []
    if has_multiple:
        rows.append([InlineKeyboardButton(text="🔀 Сменить профиль", callback_data="profile_switch")])
    rows.append([InlineKeyboardButton(text="🚪 Выйти с аккаунта", callback_data="logout")])
    rows.append([
        InlineKeyboardButton(text="🏠 Домой", callback_data="home"),
        InlineKeyboardButton(text="🔄 Обновить", callback_data="profile_refresh"),
    ])
    rows.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_profile_switch(profiles: list[tuple[str, str]], active_id: str | None) -> InlineKeyboardMarkup:
    # profiles: список (id, name)
    kb: list[list[InlineKeyboardButton]] = []
    for pid, name in profiles:
        label = f"✅ {name}" if pid == active_id else f"{name}"
        kb.append([InlineKeyboardButton(text=label, callback_data=f"set_profile:{pid}")])
    kb.append([
        InlineKeyboardButton(text="⬅️ Назад", callback_data="profile"),
        InlineKeyboardButton(text="❌ Закрыть", callback_data="close")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)
