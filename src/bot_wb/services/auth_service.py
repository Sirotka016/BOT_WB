from pathlib import Path

from ..storage.repo import UserRepo
from ..storage.session import CookieStorage
from .browser_login import BrowserLogin
from .wb_http_client import WBHttpClient


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def is_authorized(self, tg_id: int) -> bool:
        sess = Path(f"data/sessions/{tg_id}/cookies.json")
        if not sess.exists():
            await self.repo.set_authorized(tg_id, False)
            return False
        client = WBHttpClient(tg_id)
        try:
            ok = await client.is_logged_in()
            await self.repo.set_authorized(tg_id, ok)
            return ok
        finally:
            await client.aclose()

    async def interactive_login(self, tg_id: int) -> bool:
        async with BrowserLogin(tg_id) as bl:
            ok = await bl.run_flow(timeout_sec=420)
        if ok:
            client = WBHttpClient(tg_id)
            try:
                profiles = await client.list_organizations()
                await self.repo.set_profiles(tg_id, profiles)
                if profiles:
                    await self.repo.set_active_profile(tg_id, profiles[0]["id"])
                    if profiles[0].get("name"):
                        await self.repo.set_profile_org(tg_id, profiles[0]["name"])
                else:
                    org = await client.get_organization_name()
                    if org:
                        await self.repo.set_profile_org(tg_id, org)
                await self.repo.set_authorized(tg_id, True)
            finally:
                await client.aclose()
        return ok

    async def logout(self, tg_id: int):
        CookieStorage(tg_id).clear()
        await self.repo.clear_auth(tg_id)
