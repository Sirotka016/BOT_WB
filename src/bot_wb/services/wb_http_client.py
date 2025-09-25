import httpx
from httpx import Cookies

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
            response = await self.client.get("", timeout=15)
            if response.status_code != 200:
                return False
            body = response.text.lower()
            ok = (
                "seller" in body
                or "wildberries" in body
                or "<!doctype html" in body
            )
            if ok:
                self._persist()
            return ok
        except Exception:
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

    async def list_organizations(self) -> list[dict]:
        """
        TODO: заменить на реальное API WB Seller.
        Пока возвращаем 1 профиль — имя из get_organization_name().
        """
        name = await self.get_organization_name()
        return [{"id": "default", "name": name or "Аккаунт WB Seller", "inn": ""}]

    async def set_active_organization(self, org_id: str) -> bool:
        """
        TODO: если у WB действительно есть переключение юрлиц в одном логине — тут вызвать их API.
        Пока возвращаем True без запроса.
        """
        return True
