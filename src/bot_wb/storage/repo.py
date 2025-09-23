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
        query = f"""
        INSERT INTO users (tg_user_id, {keys})
        VALUES (?, {placeholders})
        ON CONFLICT(tg_user_id) DO UPDATE SET {updates}, updated_at=CURRENT_TIMESTAMP
        """
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(query, (tg_user_id, *values))
            await db.commit()

    async def set_cookies(self, tg_user_id: int, cookies: dict | None):
        cookies_json = json.dumps(cookies or {})
        await self.upsert(tg_user_id, cookies=cookies_json)

    async def clear_auth(self, tg_user_id: int):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "UPDATE users SET phone=NULL, email=NULL, cookies=NULL, is_authorized=0, "
                "updated_at=CURRENT_TIMESTAMP WHERE tg_user_id=?",
                (tg_user_id,),
            )
            await db.commit()
