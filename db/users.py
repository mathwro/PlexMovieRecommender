from __future__ import annotations

from typing import Optional
import aiosqlite

from db.database import DB_PATH


async def get_user(discord_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT discord_id, plex_token, plex_username FROM users WHERE discord_id = ?",
            (discord_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def save_user(discord_id: str, plex_token: str, plex_username: Optional[str]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (discord_id, plex_token, plex_username)
            VALUES (?, ?, ?)
            ON CONFLICT(discord_id) DO UPDATE SET
                plex_token = excluded.plex_token,
                plex_username = excluded.plex_username,
                created_at = datetime('now')
            """,
            (discord_id, plex_token, plex_username),
        )
        await db.commit()


async def delete_user(discord_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM users WHERE discord_id = ?", (discord_id,)
        )
        await db.commit()
        return cursor.rowcount > 0
