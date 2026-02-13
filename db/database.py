import aiosqlite

DB_PATH = "recommender.db"

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    discord_id TEXT PRIMARY KEY,
    plex_token TEXT NOT NULL,
    plex_username TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_USERS_TABLE)
        await db.commit()
