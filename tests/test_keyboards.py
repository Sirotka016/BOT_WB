from aiogram.types import InlineKeyboardMarkup

from bot_wb.ui.keyboards import kb_home, kb_profile_view


def _buttons_text(markup: InlineKeyboardMarkup) -> list[list[str]]:
    return [[button.text for button in row] for row in markup.inline_keyboard]


def test_home_keyboard_not_authorized():
    markup = kb_home(authorized=False)
    labels = _buttons_text(markup)
    assert labels[0] == ["🔑 Авторизация"]
    assert labels[1] == ["🔄 Обновить"]
    assert labels[2] == ["❌ Закрыть"]


def test_home_keyboard_authorized():
    markup = kb_home(authorized=True)
    labels = _buttons_text(markup)
    assert labels[0] == ["👤 Профиль"]
    assert labels[1] == ["🔄 Обновить"]
    assert labels[2] == ["❌ Закрыть"]


def test_profile_keyboard_single():
    markup = kb_profile_view(has_multiple=False)
    labels = _buttons_text(markup)
    assert ["🔀 Сменить профиль"] not in labels
    assert ["🚪 Выйти с аккаунта"] in labels


def test_profile_keyboard_multi():
    markup = kb_profile_view(has_multiple=True)
    labels = _buttons_text(markup)
    assert ["🔀 Сменить профиль"] in labels
    assert ["🚪 Выйти с аккаунта"] in labels
