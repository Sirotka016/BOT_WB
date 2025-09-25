from __future__ import annotations

import asyncio
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlparse

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from bot_wb.logging import logger
from bot_wb.settings import settings
from bot_wb.storage.session import CookieStorage

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
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._ctx: BrowserContext | None = None

    async def __aenter__(self) -> BrowserLogin:
        try:
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            self._ctx = await self._browser.new_context(
                viewport={"width": 1280, "height": 860},
            )
        except Exception as exc:
            logger.opt(exception=True).error(
                "Failed to initialize Playwright browser: {}",
                exc,
            )
            raise
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
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
        ctx = self._ctx
        if ctx is None:
            raise RuntimeError("Browser context is not initialized")
        page = await ctx.new_page()
        await page.goto(settings.wb_seller_auth_url, wait_until="domcontentloaded")

        logger.info("WB auth window opened for user {}", self.tg_user_id)

        deadline = asyncio.get_event_loop().time() + timeout_sec

        async def collect_and_check() -> bool:
            cookies = await ctx.cookies()
            jar = self._pick_cookies(cookies, WB_AUTH_DOMAINS)
            if not any(name in jar for name in IMPORTANT_COOKIES):
                return False
            storage = CookieStorage(self.tg_user_id)
            client = WBHttpClient(self.tg_user_id, storage=storage)
            try:
                client.update_cookies(jar)
                ok = await client.is_logged_in()
                if ok:
                    storage.save(jar)
                return ok
            finally:
                await client.aclose()

        while asyncio.get_event_loop().time() < deadline:
            url = page.url or ""
            host = urlparse(url).hostname or ""
            if host.endswith("seller.wildberries.ru"):
                await asyncio.sleep(1.0)
                if await collect_and_check():
                    logger.info("WB auth completed for user {}", self.tg_user_id)
                    return True
            await asyncio.sleep(1.0)

        logger.warning("WB auth timed out for user {}", self.tg_user_id)
        return False

    def _pick_cookies(
        self,
        cookies: Iterable[Mapping[str, Any]],
        allowed_domains: set[str],
    ) -> dict[str, str]:
        jar: dict[str, str] = {}
        for c in cookies:
            domain = (c.get("domain") or "").lstrip(".")
            name = c.get("name")
            value = c.get("value")
            if not name or value is None:
                continue
            if any(domain.endswith(d) for d in allowed_domains):
                jar[name] = value
        return jar
