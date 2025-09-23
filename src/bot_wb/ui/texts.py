def home_text(user_name: str) -> str:
    return (
        f"Привет, {user_name}.\n"
        f"Я бот поставок Football Shop 🤖!\n"
        f"На WB я умею бронировать поставки, искать слоты и перераспределять товары.\n"
        f"А так же создавать поставки с вашим товаром за вас!"
    )


def auth_stub_text() -> str:
    return (
        "✅ Телефон не заполнен\n"
        "✅ Авторизация не пройдена\n"
        "____________________________\n"
        "Для продолжения нужно отправить номер телефона в формате +79181234567, "
        "который используется для входа на портал WB Партнеры"
    )


def ask_phone_text() -> str:
    return "Введите номер телефона в формате +79999999999:"


def ask_sms_code_text() -> str:
    return "Введите код из СМС:"


def ask_email_code_text() -> str:
    return "Введите код с e-mail:"


def auth_success_text() -> str:
    return "✅ Авторизация выполнена. Аккаунт WB Partner привязан к вашему Telegram."


def logged_in_text() -> str:
    return "Вы уже авторизованы в WB Partner. Доступ к функциям открыт."


def logout_done_text() -> str:
    return "Вы вышли из аккаунта. Данные авторизации удалены. /start — начать заново."
