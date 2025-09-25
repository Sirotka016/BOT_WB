from __future__ import annotations

import asyncio
from typing import Any

import httpx
from httpx import AsyncBaseTransport, Cookies

from bot_wb.logging import logger
from bot_wb.settings import settings
from bot_wb.storage.session import CookieStorage

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "BOT_WB/1.0 (+tg-bot)",
    "Origin": settings.wb_seller_base,
    "Referer": settings.wb_seller_base.rstrip("/") + "/",
}


class WBHttpClient:
    """HTTP client for the WB Seller cabinet with retry/backoff logic."""

    RETRY_ATTEMPTS = 3
    RETRY_BASE_DELAY = 1.0

    def __init__(
        self,
        tg_user_id: int,
        *,
        storage: CookieStorage | None = None,
        transport: AsyncBaseTransport | None = None,
    ) -> None:
        self.tg_user_id = tg_user_id
        self._store = storage or CookieStorage(tg_user_id)
        jar = Cookies()
        for key, value in (self._store.load() or {}).items():
            jar.set(key, value)
        self.client = httpx.AsyncClient(
            base_url=settings.wb_seller_base.rstrip("/") + "/",
            headers=DEFAULT_HEADERS.copy(),
            cookies=jar,
            follow_redirects=True,
            timeout=25,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self.client.aclose()

    def update_cookies(self, jar: dict[str, str]) -> None:
        for key, value in jar.items():
            self.client.cookies.set(key, value)
        self._persist()

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        delay = self.RETRY_BASE_DELAY
        for attempt in range(1, self.RETRY_ATTEMPTS + 1):
            try:
                response = await self.client.request(method, url, **kwargs)
                self._persist()
                return response
            except httpx.RequestError as exc:
                logger.warning(
                    "WB request {} {} failed on attempt {}: {}",
                    method,
                    url,
                    attempt,
                    exc,
                )
                if attempt == self.RETRY_ATTEMPTS:
                    raise
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError("unreachable")

    def _persist(self) -> None:
        self._store.save(
            {cookie.name: cookie.value for cookie in self.client.cookies.jar},
        )

    async def is_logged_in(self) -> bool:
        try:
            response = await self._request("GET", "", timeout=15)
        except httpx.HTTPError as exc:
            logger.info("WB auth health-check failed: {}", exc)
            return False
        if response.status_code != httpx.codes.OK:
            logger.info(
                "WB auth health-check returned unexpected status {}",
                response.status_code,
            )
            return False
        body = response.text.lower()
        ok = "seller" in body or "wildberries" in body or "<!doctype html" in body
        if not ok:
            logger.info("WB auth health-check body did not look valid")
        return ok

    async def get_organization_name(self) -> str | None:
        try:
            response = await self._request("GET", "")
        except httpx.HTTPError as exc:
            logger.info("WB profile fetch failed: {}", exc)
            return None
        if response.status_code == httpx.codes.OK:
            return "Аккаунт WB Seller"
        return None

    async def list_organizations(self) -> list[dict[str, str]]:
        """Placeholder that returns a single pseudo profile.

        TODO: заменить на реальное API WB Seller, когда ручка будет доступна.
        """

        name = await self.get_organization_name()
        return [
            {
                "id": "default",
                "name": name or "Аккаунт WB Seller",
                "inn": "",
            },
        ]

    async def set_active_organization(self, org_id: str) -> bool:
        """Placeholder for WB profile switching (real API to be added later).

        TODO: заменить на реальную ручку WB, когда появится документация.
        """

        _ = org_id
        return True
