import json
import aiosqlite

from .db import DB_PATH


class UserRepo:
    def __init__(self, db_path=DB_PATH):
        self._db_path = db_path

    async def get(self, tg_user_id: int):
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE tg_user_id=?", (tg_user_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def upsert(self, tg_user_id: int, **fields):
        if not fields:
            return
        keys = ", ".join(fields.keys())
        placeholders = ", ".join(["?"] * len(fields))
        updates = ", ".join([f"{k}=excluded.{k}" for k in fields.keys()])
        values = list(fields.values())
        q = (
            f"INSERT INTO users (tg_user_id,{keys}) VALUES (?,{placeholders}) "
            f"ON CONFLICT(tg_user_id) DO UPDATE SET {updates}, updated_at=CURRENT_TIMESTAMP"
        )
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(q, (tg_user_id, *values))
            await db.commit()

    async def set_anchor(self, tg_user_id: int, msg_id: int):
        await self.upsert(tg_user_id, anchor_msg_id=msg_id)

    async def get_anchor(self, tg_user_id: int) -> int | None:
        u = await self.get(tg_user_id)
        return u.get("anchor_msg_id") if u else None

    async def set_view(self, tg_user_id: int, view: str | None):
        await self.upsert(tg_user_id, current_view=view)

    async def get_view(self, tg_user_id: int) -> str | None:
        u = await self.get(tg_user_id)
        return u.get("current_view") if u else None

    async def set_authorized(self, tg_user_id: int, flag: bool):
        await self.upsert(tg_user_id, is_authorized=1 if flag else 0)

    async def is_authorized(self, tg_user_id: int) -> bool:
        u = await self.get(tg_user_id)
        return bool(u and u.get("is_authorized"))

    async def set_profile_org(self, tg_user_id: int, org: str | None):
        await self.upsert(tg_user_id, profile_org=org)

    async def clear_auth(self, tg_user_id: int):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE users SET phone=NULL,email=NULL,cookies=NULL,api_token=NULL,"
                "is_authorized=0,profile_org=NULL,current_view=NULL,profiles_json=NULL,"
                "active_profile_id=NULL,updated_at=CURRENT_TIMESTAMP "
                "WHERE tg_user_id=?",
                (tg_user_id,),
            )
            await db.commit()

    async def set_profiles(self, tg_user_id: int, profiles: list[dict]):
        await self.upsert(tg_user_id, profiles_json=json.dumps(profiles, ensure_ascii=False))

    async def get_profiles(self, tg_user_id: int) -> list[dict]:
        u = await self.get(tg_user_id)
        if not u or not u.get("profiles_json"):
            return []
        try:
            return json.loads(u["profiles_json"])
        except Exception:
            return []

    async def set_active_profile(self, tg_user_id: int, profile_id: str):
        await self.upsert(tg_user_id, active_profile_id=profile_id)

    async def get_active_profile(self, tg_user_id: int) -> str | None:
        u = await self.get(tg_user_id)
        return u.get("active_profile_id") if u else None
