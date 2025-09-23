from ..storage.repo import UserRepo
from .wb_http_client import WBHttpClient


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def is_authorized(self, tg_id: int) -> bool:
        return await self.repo.is_authorized(tg_id)

    async def login_phone(self, tg_id: int, phone: str) -> bool:
        client = WBHttpClient()
        try:
            ok = await client.start_phone(phone)
            if ok:
                await self.repo.upsert(tg_id, phone=phone)
            return ok
        finally:
            await client.aclose()

    async def login_sms(self, tg_id: int, phone: str, code: str) -> bool:
        client = WBHttpClient()
        try:
            return await client.confirm_sms(phone, code)
        finally:
            await client.aclose()

    async def login_email_code(self, tg_id: int, code: str) -> bool:
        client = WBHttpClient()
        try:
            ok = await client.confirm_email_code(code)
            if ok:
                org = await client.get_profile_org()
                await self.repo.set_authorized(tg_id, True)
                if org:
                    await self.repo.set_profile_org(tg_id, org)
            return ok
        finally:
            await client.aclose()

    async def logout(self, tg_id: int):
        await self.repo.clear_auth(tg_id)
