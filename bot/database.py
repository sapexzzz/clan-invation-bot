import time
from datetime import datetime
from typing import Optional

import aiosqlite

DB_PATH = "clan_bot.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                last_application_time REAL,
                is_blocked INTEGER NOT NULL DEFAULT 0
            )
        """)
        # Миграция для существующих БД без колонки is_blocked
        try:
            await db.execute("ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass  # Колонка уже существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                username TEXT,
                nickname TEXT,
                game_id TEXT,
                rank_comp TEXT,
                rank_allies TEXT,
                rank_duels TEXT,
                hours INTEGER,
                kd REAL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT,
                group_message_id INTEGER
            )
        """)
        await db.commit()


# ─── Users ────────────────────────────────────────────────────────────────────

async def get_user(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def upsert_user_timestamp(telegram_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, last_application_time)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET last_application_time = excluded.last_application_time
        """, (telegram_id, time.time()))
        await db.commit()


async def get_last_application_time(telegram_id: int) -> Optional[float]:
    user = await get_user(telegram_id)
    if user:
        return user.get("last_application_time")
    return None


# ─── Applications ─────────────────────────────────────────────────────────────

async def create_application(
    telegram_id: int,
    username: Optional[str],
    nickname: str,
    game_id: str,
    rank_comp: str,
    rank_allies: str,
    rank_duels: str,
    hours: int,
    kd: float,
    status: str = "pending",
    group_message_id: Optional[int] = None,
) -> int:
    created_at = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO applications
                (telegram_id, username, nickname, game_id, rank_comp, rank_allies,
                 rank_duels, hours, kd, status, created_at, group_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telegram_id, username, nickname, game_id, rank_comp, rank_allies,
            rank_duels, hours, kd, status, created_at, group_message_id,
        ))
        await db.commit()
        return cursor.lastrowid


async def update_application_status(
    app_id: int,
    status: str,
    group_message_id: Optional[int] = None,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        if group_message_id is not None:
            await db.execute(
                "UPDATE applications SET status = ?, group_message_id = ? WHERE id = ?",
                (status, group_message_id, app_id),
            )
        else:
            await db.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (status, app_id),
            )
        await db.commit()


async def get_application_by_id(app_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def is_user_blocked(telegram_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT is_blocked FROM users WHERE telegram_id = ?", (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row and row[0])


async def block_user(telegram_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, is_blocked)
            VALUES (?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET is_blocked = 1
        """, (telegram_id,))
        await db.commit()


async def unblock_user(telegram_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_blocked = 0 WHERE telegram_id = ?", (telegram_id,)
        )
        await db.commit()


async def get_all_users_stats() -> list[dict]:
    """Все пользователи с агрегированной статистикой заявок."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT
                u.telegram_id,
                u.is_blocked,
                u.last_application_time,
                COUNT(a.id)                                        AS total,
                SUM(CASE WHEN a.status='pending'       THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN a.status='accepted'      THEN 1 ELSE 0 END) AS accepted,
                SUM(CASE WHEN a.status='rejected'      THEN 1 ELSE 0 END) AS rejected,
                SUM(CASE WHEN a.status='rejected_auto' THEN 1 ELSE 0 END) AS rejected_auto,
                MAX(a.username)                                    AS username,
                MAX(a.nickname)                                    AS nickname
            FROM users u
            LEFT JOIN applications a ON a.telegram_id = u.telegram_id
            GROUP BY u.telegram_id
            ORDER BY u.last_application_time DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_pending_application(telegram_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM applications WHERE telegram_id = ? AND status = 'pending' LIMIT 1",
            (telegram_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
