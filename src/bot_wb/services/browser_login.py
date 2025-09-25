import asyncio
from urllib.parse import urlparse
from typing import Any, Dict, Iterable

from loguru import logger
from playwright.async_api import Browser, BrowserContext, async_playwright

from ..settings import settings
from .wb_http_client import WBHttpClient

WB_AUTH_DOMAINS = {"seller-auth.wildberries.ru", "seller.wildberries.ru"}

IMPORTANT_COOKIES = {
    "wbx-validation-key",
    "wbx-refresh",
}


class BrowserLogin:
    """
    Открывает реальное окно авторизации WB Seller. Пользователь проходит вход вручную.
    После редиректа/успешного входа — сохраняем куки для доменов WB_AUTH_DOMAINS.
    """

    def __init__(self, tg_user_id: int):
        self.tg_user_id = tg_user_id
        self._pw = None
        self._browser: Browser | None = None
        self._ctx: BrowserContext | None = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._ctx = await self._browser.new_context(viewport={"width": 1280, "height": 860})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if self._ctx:
                await self._ctx.close()
        finally:
            if self._browser:
                await self._browser.close()
            if self._pw:
                await self._pw.stop()

    async def run_flow(self, timeout_sec: int = 420) -> bool:
        """
        Открывает страницу логина и ждёт реальную валидную сессию.
        Успех фиксируется только после появления нужных cookie и успешной HTTP-проверки.
        """

        assert self._ctx is not None
        page = await self._ctx.new_page()
        await page.goto(settings.wb_seller_auth_url, wait_until="domcontentloaded")

        logger.info("WB auth window opened. User should complete login in the browser window.")

        deadline = asyncio.get_event_loop().time() + timeout_sec

        async def collect_and_check() -> bool:
            cookies = await self._ctx.cookies()
            jar = self._pick_cookies(cookies, WB_AUTH_DOMAINS)
            if not any(name in jar for name in IMPORTANT_COOKIES):
                return False
            client = WBHttpClient(self.tg_user_id)
            try:
                client.client.cookies.update(jar)
                return await client.is_logged_in()
            finally:
                await client.aclose()

        while asyncio.get_event_loop().time() < deadline:
            url = page.url or ""
            host = urlparse(url).hostname or ""
            if host.endswith("seller.wildberries.ru"):
                await asyncio.sleep(1.0)
                if await collect_and_check():
                    return True
            await asyncio.sleep(1.0)

        return False

    def _pick_cookies(
        self,
        cookies: Iterable[Dict[str, Any]],
        allowed_domains: set[str],
    ) -> Dict[str, str]:
        jar: Dict[str, str] = {}
        for c in cookies:
            domain = (c.get("domain") or "").lstrip(".")
            name = c.get("name")
            value = c.get("value")
            if not name or value is None:
                continue
            if any(domain.endswith(d) for d in allowed_domains):
                jar[name] = value
        return jar
