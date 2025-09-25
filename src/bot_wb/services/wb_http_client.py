import httpx
from httpx import Cookies
from loguru import logger

from ..settings import settings
from ..storage.session import CookieStorage

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "BOT_WB/1.0 (+tg-bot)",
    "Origin": settings.wb_seller_base,
    "Referer": settings.wb_seller_base + "/",
}


class WBHttpClient:
    """
    Быстрые HTTP-запросы к WB после ручной авторизации в браузере.
    Куки подтягиваем из data/sessions/<tg_id>/cookies.json
    """

    def __init__(self, tg_user_id: int):
        self.tg_user_id = tg_user_id
        store = CookieStorage(tg_user_id)
        jar = Cookies()
        for k, v in (store.load() or {}).items():
            jar.set(k, v)
        self.client = httpx.AsyncClient(
            base_url=settings.wb_seller_base.rstrip("/") + "/",
            headers=DEFAULT_HEADERS.copy(),
            cookies=jar,
            follow_redirects=True,
            timeout=25,
        )
        self._store = store

    async def aclose(self):
        await self.client.aclose()

    def _persist(self):
        self._store.save({c.name: c.value for c in self.client.cookies.jar})

    async def is_logged_in(self) -> bool:
        try:
            response = await self.client.get("")
            self._persist()
            return response.status_code == 200 and (
                "<!DOCTYPE html" in response.text or "seller" in response.text.lower()
            )
        except Exception as exc:
            logger.warning(f"is_logged_in error: {exc}")
            return False

    async def get_organization_name(self) -> str | None:
        try:
            response = await self.client.get("")
            self._persist()
            if response.status_code == 200:
                return "Аккаунт WB Seller"
        except Exception:
            pass
        return None
