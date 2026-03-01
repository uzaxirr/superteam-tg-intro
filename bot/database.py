import os
import aiosqlite
from bot.config import DB_PATH

STATUS_PENDING = "pending"
STATUS_INTRODUCED = "introduced"


async def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                intro_message_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                introduced_at TIMESTAMP
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str | None, full_name: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name, STATUS_PENDING),
        )
        await db.commit()


async def get_user(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def mark_introduced(user_id: int, message_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE users
            SET status = ?, intro_message_id = ?, introduced_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (STATUS_INTRODUCED, message_id, user_id),
        )
        await db.commit()


async def reset_user(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            UPDATE users SET status = ?, intro_message_id = NULL, introduced_at = NULL
            WHERE user_id = ?
            """,
            (STATUS_PENDING, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            total = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE status = ?", (STATUS_PENDING,)
        ) as cur:
            pending = (await cur.fetchone())[0]
        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE status = ?", (STATUS_INTRODUCED,)
        ) as cur:
            introduced = (await cur.fetchone())[0]
    return {"total": total, "pending": pending, "introduced": introduced}
