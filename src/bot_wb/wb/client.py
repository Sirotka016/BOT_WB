import asyncio
import json
from typing import Any, Awaitable, Callable, Dict

import httpx
from httpx import Cookies
from loguru import logger

from ..settings import settings
from ..storage.session import CookieStorage
from .errors import WBRateLimit, WBUnexpectedResponse

DEFAULT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "BOT_WB/1.0 (+https://example.local)",
    "Origin": settings.wb_seller_base,
    "Referer": settings.wb_seller_base + "/",
}


class WBClient:
    """
    Клиент с общей сессией/ретраями.
    Один инстанс — на одного TG-пользователя.
    """

    def __init__(self, tg_user_id: int):
        self.tg_user_id = tg_user_id
        self._store = CookieStorage(tg_user_id)
        jar = Cookies()
        for k, v in (self._store.load() or {}).items():
            jar.set(k, v)
        self.http = httpx.AsyncClient(
            base_url=settings.wb_seller_base.rstrip("/") + "/",
            headers=DEFAULT_HEADERS.copy(),
            cookies=jar,
            follow_redirects=True,
            timeout=25,
        )

    async def aclose(self) -> None:
        await self.http.aclose()

    def _persist(self) -> None:
        self._store.save({c.name: c.value for c in self.http.cookies.jar})

    async def _retry(
        self, fn: Callable[[], Awaitable[httpx.Response]], tries: int = 3
    ) -> httpx.Response:
        delay = 0.5
        for i in range(tries):
            try:
                resp = await fn()
                if resp.status_code in (429, 503):
                    raise WBRateLimit(f"Rate limited: {resp.status_code}")
                return resp
            except WBRateLimit:
                if i == tries - 1:
                    raise
                logger.warning("WB rate limited, retrying in {delay}s", delay=delay)
                await asyncio.sleep(delay)
                delay *= 2
            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.RemoteProtocolError,
            ) as exc:
                if i == tries - 1:
                    raise
                logger.warning(
                    "WB request error {name}, retrying in {delay:.1f}s",
                    name=exc.__class__.__name__,
                    delay=delay,
                )
                await asyncio.sleep(delay)
                delay *= 2
        raise WBUnexpectedResponse("WB retry logic exhausted without response")

    async def get_json(self, url: str, **kw: Any) -> Dict[str, Any]:
        r = await self._retry(lambda: self.http.get(url, **kw))
        self._persist()
        try:
            return r.json()
        except json.JSONDecodeError:
            raise WBUnexpectedResponse(f"JSON expected at {url}, got {r.text[:200]}")

    async def post_json(
        self, url: str, json_body: Dict[str, Any], **kw: Any
    ) -> Dict[str, Any]:
        r = await self._retry(lambda: self.http.post(url, json=json_body, **kw))
        self._persist()
        try:
            return r.json()
        except json.JSONDecodeError:
            raise WBUnexpectedResponse(f"JSON expected at {url}, got {r.text[:200]}")
