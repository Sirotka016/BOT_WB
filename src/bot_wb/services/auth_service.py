from bot_wb.logging import logger
from bot_wb.storage.repo import UserRepo
from bot_wb.storage.session import CookieStorage

from .browser_login import BrowserLogin
from .wb_http_client import WBHttpClient


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def is_authorized(self, tg_id: int) -> bool:
        storage = CookieStorage(tg_id)
        if not storage.cookies_path.exists():
            await self.repo.set_authorized(tg_id, False)
            return False
        client = WBHttpClient(tg_id, storage=storage)
        try:
            ok = await client.is_logged_in()
            await self.repo.set_authorized(tg_id, ok)
            return ok
        finally:
            await client.aclose()

    async def interactive_login(self, tg_id: int) -> bool:
        logger.info("Starting interactive login for user {}", tg_id)
        async with BrowserLogin(tg_id) as bl:
            ok = await bl.run_flow(timeout_sec=420)
        if ok:
            logger.info("Interactive login succeeded for user {}", tg_id)
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
        else:
            logger.warning("Interactive login failed for user {}", tg_id)
            await self.repo.set_authorized(tg_id, False)
        return ok

    async def logout(self, tg_id: int):
        logger.info("Clearing session for user {}", tg_id)
        CookieStorage(tg_id).clear()
        await self.repo.clear_auth(tg_id)
