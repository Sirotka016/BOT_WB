def home_text(user_name: str, authorized: bool) -> str:
    base = (
        f"Привет, {user_name}.\n"
        f"Я бот поставок Football Shop 🤖!\n"
        f"На WB я умею бронировать поставки, искать слоты и перераспределять товары.\n"
        f"А так же создавать поставки с вашим товаром за вас!"
    )
    if authorized:
        base += "\n\n✅ Вы авторизованы в WB Partner."
    return base


def ask_phone_text() -> str:
    return "Введите номер телефона в формате +79999999999:"


def ask_sms_code_text() -> str:
    return "Введите код из СМС:"


def ask_email_code_text() -> str:
    return "Введите код с e-mail:"


def auth_success_text() -> str:
    return "✅ Авторизация выполнена. Аккаунт привязан к вашему Telegram."


def profile_text(org: str | None) -> str:
    org_line = f"Организация: {org}" if org else "Организация: —"
    return f"👤 Профиль WB Partner\n{org_line}"


def logout_done_text() -> str:
    return "Вы вышли из аккаунта. Нажмите /start для новой сессии."
