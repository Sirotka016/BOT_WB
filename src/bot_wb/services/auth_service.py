from pathlib import Path

from ..settings import settings
from ..storage.repo import UserRepo
from ..storage.session import CookieStorage
from .wb_http_client import WBHttpClient


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def is_authorized(self, tg_id: int) -> bool:
        u = await self.repo.get(tg_id)
        sess_file = Path(f"data/sessions/{tg_id}/cookies.json")
        return bool(u and u.get("is_authorized") and sess_file.exists())

    async def _client_for(self, tg_id: int) -> tuple[WBHttpClient, CookieStorage]:
        store = CookieStorage(tg_id)
        client = WBHttpClient(settings.wb_partner_url, cookies=store.load())
        return client, store

    async def login_phone(self, tg_id: int, phone: str) -> bool:
        client, store = await self._client_for(tg_id)
        try:
            ok = await client.start_phone(phone)
            store.save(client.export_cookies())
            if ok:
                await self.repo.upsert(tg_id, phone=phone)
            return ok
        finally:
            await client.aclose()

    async def login_sms(self, tg_id: int, phone: str, code: str) -> bool:
        client, store = await self._client_for(tg_id)
        try:
            ok = await client.confirm_sms(phone, code)
            store.save(client.export_cookies())
            return ok
        finally:
            await client.aclose()

    async def login_email_code(self, tg_id: int, code: str) -> bool:
        client, store = await self._client_for(tg_id)
        try:
            ok = await client.confirm_email_code(code)
            store.save(client.export_cookies())
            if ok:
                org = await client.get_profile_org()
                await self.repo.set_authorized(tg_id, True)
                if org:
                    await self.repo.set_profile_org(tg_id, org)
            return ok
        finally:
            await client.aclose()

    async def logout(self, tg_id: int):
        CookieStorage(tg_id).clear()
        await self.repo.clear_auth(tg_id)
