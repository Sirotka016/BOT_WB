import httpx
from loguru import logger


class WBHttpClient:
    """
    HTTP-клиент для авторизации в WB Seller.
    !!! ЗАПОЛНИТЕ TODO: реальные URL, заголовки, схемы тел/ответов.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=20, follow_redirects=True)

    async def aclose(self):
        await self.client.aclose()

    async def start_phone(self, phone: str) -> bool:
        # TODO: POST на отправку СМС
        # resp = await self.client.post("https://.../auth/phone", json={"phone": phone})
        # return resp.status_code == 200 and resp.json().get("ok")
        logger.info(f"[WB] start_phone {phone=}")
        return True

    async def confirm_sms(self, phone: str, code: str) -> bool:
        # TODO: POST подтверждения СМС; сервер должен выдать промежуточную сессию
        logger.info(f"[WB] confirm_sms {phone=} code=****")
        # пример: self.client.cookies.update(resp.cookies)
        return True

    async def confirm_email_code(self, code: str) -> bool:
        # TODO: POST подтверждения кода с почты; после этого сессия считается полной
        logger.info("[WB] confirm_email_code ****")
        return True

    async def get_profile_org(self) -> str | None:
        # TODO: GET профиль/организация в авторизованной сессии
        # r = await self.client.get("https://.../profile")
        # return r.json().get("orgName")
        logger.info("[WB] get_profile_org")
        return "ООО «Пример»"
