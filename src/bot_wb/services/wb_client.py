import httpx
from loguru import logger

from ..settings import settings


class WBClient:
    """
    Адаптер к WB Partner. Здесь только заготовки — нужно подставить реальные эндпойнты
    и payload'ы, когда дадите спецификацию.
    """

    def __init__(self, cookies: dict | None = None):
        self._jar = httpx.Cookies()
        for key, value in (cookies or {}).items():
            self._jar.set(key, value)
        self._client = httpx.AsyncClient(
            base_url=settings.wb_base_url,
            cookies=self._jar,
            timeout=30,
        )

    async def aclose(self):
        await self._client.aclose()

    def export_cookies(self) -> dict:
        return {cookie.name: cookie.value for cookie in self._client.cookies.jar}

    async def start_phone_auth(self, phone: str) -> bool:
        """
        Отправить телефон на WB, чтобы выслали СМС-код.
        TODO: заменить на реальный POST /auth/phone, параметры и проверку ответа.
        """
        logger.info("[WB] start_phone_auth phone={phone}", phone=phone)
        # response = await self._client.post("/auth/phone", json={"phone": phone})
        # return response.status_code == 200 and response.json().get("ok")
        return True

    async def confirm_sms_code(self, phone: str, code: str) -> bool:
        """
        Подтвердить код из СМС, сервер установит auth cookies.
        TODO: заменить на реальный POST /auth/phone/confirm
        """
        logger.info("[WB] confirm_sms_code phone={phone}, code=****", phone=phone)
        # response = await self._client.post(
        #     "/auth/phone/confirm",
        #     json={"phone": phone, "code": code},
        # )
        # return response.status_code == 200 and response.json().get("ok")
        self._client.cookies.set("sessionid", "fake-session")
        return True

    async def submit_email(self, email: str) -> bool:
        """
        Отправить e-mail для 2FA.
        TODO: реальный POST /auth/email
        """
        logger.info("[WB] submit_email email={email}", email=email)
        return True

    async def confirm_email_code(self, email: str, code: str) -> bool:
        """
        Подтверждение кода из письма. После успеха сессия полностью авторизована.
        TODO: реальный POST /auth/email/confirm
        """
        logger.info("[WB] confirm_email_code email={email}, code=****", email=email)
        return True
