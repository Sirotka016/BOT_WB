from loguru import logger

from .client import WBClient
from .errors import WBAuthError
from .utils import normalize_ru_phone_e164


class AuthAPI:
    """
    Авторизация: телефон -> sms -> email_code.
    Все реальные пути/поля отметены как TODO.
    """

    def __init__(self, client: WBClient):
        self.c = client

    async def start_phone(self, phone_raw: str) -> bool:
        phone = normalize_ru_phone_e164(phone_raw)
        if not phone:
            raise WBAuthError("Bad phone format")
        # TODO: возможно потребуется initial GET, чтобы получить csrf
        # html = await self.c.http.get("").text; csrf = pick_csrf_from_html(html)

        # TODO: заменить путь/тело запроса:
        data = {"phone": phone}
        resp = await self.c.post_json("api/auth/phone", json_body=data)
        ok = bool(resp.get("ok", True))  # подставь правильную проверку
        logger.info(f"auth.start_phone -> {ok}")
        return ok

    async def confirm_sms(self, phone_raw: str, code: str) -> bool:
        phone = normalize_ru_phone_e164(phone_raw)
        data = {"phone": phone, "code": code}
        resp = await self.c.post_json("api/auth/phone/confirm", json_body=data)  # TODO
        ok = bool(resp.get("ok", True))
        logger.info(f"auth.confirm_sms -> {ok}")
        return ok

    async def confirm_email_code(self, code: str) -> bool:
        data = {"code": code}
        resp = await self.c.post_json("api/auth/email/confirm", json_body=data)  # TODO
        ok = bool(resp.get("ok", True))
        logger.info(f"auth.confirm_email -> {ok}")
        return ok
