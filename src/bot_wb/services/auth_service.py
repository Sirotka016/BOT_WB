from pathlib import Path

from ..storage.repo import UserRepo
from ..storage.session import CookieStorage
from ..wb import WBSeller


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def is_authorized(self, tg_id: int) -> bool:
        u = await self.repo.get(tg_id)
        sess_file = Path(f"data/sessions/{tg_id}/cookies.json")
        return bool(u and u.get("is_authorized") and sess_file.exists())

    async def login_phone(self, tg_id: int, phone: str) -> bool:
        wb = WBSeller(tg_id)
        try:
            ok = await wb.auth.start_phone(phone)
            if ok:
                await self.repo.upsert(tg_id, phone=phone)
            return ok
        finally:
            await wb.aclose()

    async def login_sms(self, tg_id: int, phone: str, code: str) -> bool:
        wb = WBSeller(tg_id)
        try:
            return await wb.auth.confirm_sms(phone, code)
        finally:
            await wb.aclose()

    async def login_email_code(self, tg_id: int, code: str) -> bool:
        wb = WBSeller(tg_id)
        try:
            ok = await wb.auth.confirm_email_code(code)
            if ok:
                org = await wb.profile.organization()
                if org:
                    await self.repo.set_profile_org(tg_id, org["name"])
                await self.repo.set_authorized(tg_id, True)
            return ok
        finally:
            await wb.aclose()

    async def logout(self, tg_id: int):
        CookieStorage(tg_id).clear()
        await self.repo.clear_auth(tg_id)
