from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def kb_home(authorized: bool) -> InlineKeyboardMarkup:
    row1 = []
    if authorized:
        row1.append(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
        # ВАЖНО: на главном больше ничего не добавляем, ты просил только Профиль/Домой/Закрыть (Домой = этот экран)
    else:
        row1.append(InlineKeyboardButton(text="🔑 Авторизация", callback_data="auth"))
    # Домой = этот экран, отдельной кнопки не нужно — мы и так «дома»
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [*row1],
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


def kb_profile_view(has_multiple: bool) -> InlineKeyboardMarkup:
    rows = []
    # В профиле должны быть кнопки: Сменить профиль, Выйти, Домой, Обновить, Закрыть
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
