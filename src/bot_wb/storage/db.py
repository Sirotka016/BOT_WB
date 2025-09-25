from pathlib import Path

import aiosqlite

DB_PATH = Path("data/bot.db")

INIT_SQL = """
CREATE TABLE IF NOT EXISTS users (
    tg_user_id INTEGER PRIMARY KEY,
    phone TEXT,
    email TEXT,
    cookies TEXT,
    api_token TEXT,
    is_authorized INTEGER DEFAULT 0,
    profile_org TEXT,
    anchor_msg_id INTEGER,
    current_view TEXT,
    profiles_json TEXT,
    active_profile_id TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(INIT_SQL)
        # миграции для уже существующих таблиц
        cols = {
            r[1]
            for r in await (await db.execute("PRAGMA table_info(users)")).fetchall()
        }
        for col, ddl in [
            ("profile_org", "ALTER TABLE users ADD COLUMN profile_org TEXT"),
            ("anchor_msg_id", "ALTER TABLE users ADD COLUMN anchor_msg_id INTEGER"),
            ("current_view", "ALTER TABLE users ADD COLUMN current_view TEXT"),
            ("api_token", "ALTER TABLE users ADD COLUMN api_token TEXT"),
            ("profiles_json", "ALTER TABLE users ADD COLUMN profiles_json TEXT"),
            (
                "active_profile_id",
                "ALTER TABLE users ADD COLUMN active_profile_id TEXT",
            ),
        ]:
            if col not in cols:
                await db.execute(ddl)
        await db.commit()
