import httpx
from httpx import Cookies
from loguru import logger
from typing import Any, Dict

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 BOT_WB/1.0",
}


class WBHttpClient:
    """
    HTTP-клиент WB Seller.
    Здесь НЕ раскрыты закрытые эндпоинты: помечены как TODO.
    Мы обеспечиваем скорость за счёт постоянной сессии (cookies) и httpx.
    """

    def __init__(self, base_url: str, cookies: Dict[str, Any] | None = None):
        jar = Cookies()
        for k, v in (cookies or {}).items():
            jar.set(k, v)
        self.client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers=DEFAULT_HEADERS,
            timeout=20,
            cookies=jar,
            follow_redirects=True,
        )

    async def aclose(self):
        await self.client.aclose()

    def export_cookies(self) -> Dict[str, Any]:
        # httpx.Cookies → dict
        return {c.name: c.value for c in self.client.cookies.jar}

    # ------------------- AUTH FLOW (заполни TODO) -------------------

    async def start_phone(self, phone_e164: str) -> bool:
        """
        Шаг 1: отправить телефон, чтобы сервер отправил СМС.
        TODO: подставить реальный URL/тело запроса/проверку ответа.
        """
        logger.info(f"[WB] start_phone {phone_e164=}")
        # resp = await self.client.post("auth/phone", json={"phone": phone_e164})
        # return resp.status_code == 200 and resp.json().get("ok")
        return True

    async def confirm_sms(self, phone_e164: str, code: str) -> bool:
        """
        Шаг 2: подтвердить код из СМС. Сервер может выдать промежуточные cookies.
        """
        logger.info(f"[WB] confirm_sms phone=**** code=****")
        # resp = await self.client.post("auth/phone/confirm", json={"phone": phone_e164, "code": code})
        # return resp.status_code == 200 and resp.json().get("ok")
        return True

    async def confirm_email_code(self, code: str) -> bool:
        """
        Шаг 3: подтвердить код из e-mail и завершить вход.
        """
        logger.info(f"[WB] confirm_email_code code=****")
        # resp = await self.client.post("auth/email/confirm", json={"code": code})
        # return resp.status_code == 200 and resp.json().get("ok")
        return True

    async def get_profile_org(self) -> str | None:
        """
        Прочитать «Организацию» из ЛК (после входа).
        """
        logger.info("[WB] get_profile_org")
        # r = await self.client.get("profile")
        # return r.json().get("organizationName")
        return "ООО «Пример»"
