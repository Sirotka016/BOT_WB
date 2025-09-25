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


def profile_text_single(org_name: str | None) -> str:
    org_line = f"Организация: {org_name}" if org_name else "Организация: —"
    return f"👤 Профиль WB Seller\n{org_line}"


def profile_text_multi(orgs: list[dict], active_id: str | None) -> str:
    lines = ["👤 Профили WB Seller:"]
    for x in orgs:
        mark = "✅" if x.get("id") == active_id else "•"
        name = x.get("name") or "—"
        inn = f" (ИНН {x.get('inn')})" if x.get("inn") else ""
        lines.append(f"{mark} {name}{inn} — id: {x.get('id')}")
    return "\n".join(lines)


def logout_done_text() -> str:
    return "Вы вышли из аккаунта. Нажмите /start для новой сессии."
