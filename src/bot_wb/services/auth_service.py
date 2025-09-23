from dataclasses import dataclass
from loguru import logger

from ..storage.repo import UserRepo
from .wb_client import WBClient


def _load_cookies(data: str | None) -> dict:
    if not data:
        return {}
    try:
        import json

        return json.loads(data)
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to load cookies: {exc}", exc=exc)
        return {}


@dataclass
class AuthState:
    phone: str | None = None
    email: str | None = None


class AuthService:
    def __init__(self, repo: UserRepo):
        self.repo = repo

    async def is_authorized(self, tg_user_id: int) -> bool:
        user = await self.repo.get(tg_user_id)
        if not user or not user.get("is_authorized"):
            return False
        cookies = _load_cookies(user.get("cookies"))
        return bool(cookies)

    async def get_client(self, tg_user_id: int) -> WBClient:
        user = await self.repo.get(tg_user_id)
        cookies = _load_cookies(user.get("cookies")) if user else {}
        return WBClient(cookies=cookies)

    async def start_by_phone(self, tg_user_id: int, phone: str) -> bool:
        client = await self.get_client(tg_user_id)
        try:
            ok = await client.start_phone_auth(phone)
            if ok:
                await self.repo.upsert(tg_user_id, phone=phone, email=None, is_authorized=0)
                await self.repo.set_cookies(tg_user_id, None)
            return ok
        finally:
            await client.aclose()

    async def confirm_sms(self, tg_user_id: int, code: str) -> bool:
        user = await self.repo.get(tg_user_id)
        if not user or not user.get("phone"):
            return False
        client = await self.get_client(tg_user_id)
        try:
            ok = await client.confirm_sms_code(user["phone"], code)
            if ok:
                await self.repo.set_cookies(tg_user_id, client.export_cookies())
            return ok
        finally:
            await client.aclose()

    async def submit_email(self, tg_user_id: int, email: str) -> bool:
        client = await self.get_client(tg_user_id)
        try:
            ok = await client.submit_email(email)
            if ok:
                await self.repo.upsert(tg_user_id, email=email)
            return ok
        finally:
            await client.aclose()

    async def confirm_email(self, tg_user_id: int, code: str) -> bool:
        user = await self.repo.get(tg_user_id)
        if not user or not user.get("email"):
            return False
        client = await self.get_client(tg_user_id)
        try:
            ok = await client.confirm_email_code(user["email"], code)
            if ok:
                await self.repo.upsert(tg_user_id, is_authorized=1)
            return ok
        finally:
            await client.aclose()

    async def logout(self, tg_user_id: int):
        logger.info("Logout tg_user_id={tg_user_id}", tg_user_id=tg_user_id)
        await self.repo.clear_auth(tg_user_id)
