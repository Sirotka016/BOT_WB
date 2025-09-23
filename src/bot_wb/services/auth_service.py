from ..settings import settings
from ..storage.repo import UserRepo
from .wb_browser import WBBrowser


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo
        self.browser = WBBrowser(settings.wb_partner_url)

    async def is_authorized(self, tg_user_id: int) -> bool:
        return await self.browser.is_logged_in(tg_user_id)

    async def start_partner(self, tg_user_id: int):
        await self.browser.open_partner(tg_user_id)

    async def submit_phone(self, tg_user_id: int, phone: str):
        await self.browser.fill_phone(tg_user_id, phone)

    async def submit_sms(self, tg_user_id: int, code: str):
        await self.browser.fill_sms_code(tg_user_id, code)

    async def submit_email(self, tg_user_id: int, email: str):
        await self.browser.fill_email(tg_user_id, email)

    async def submit_email_code(self, tg_user_id: int, code: str):
        await self.browser.fill_email_code(tg_user_id, code)

    async def logout(self, tg_user_id: int):
        await self.browser.logout(tg_user_id)
        await self.repo.clear_auth(tg_user_id)
