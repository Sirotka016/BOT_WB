import aiosqlite
from pathlib import Path

DB_PATH = Path("data/bot.db")

INIT_SQL = """
CREATE TABLE IF NOT EXISTS users (
    tg_user_id INTEGER PRIMARY KEY,
    phone TEXT,
    email TEXT,
    cookies TEXT,
    is_authorized INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def ensure_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(INIT_SQL)
        await db.commit()
