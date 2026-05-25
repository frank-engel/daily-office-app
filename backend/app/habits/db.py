import datetime
from pathlib import Path
from typing import Optional

import aiosqlite

DB_PATH = Path(__file__).parent.parent.parent / "data" / "habits.sqlite"

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS completions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT,
    date         TEXT NOT NULL,
    office       TEXT NOT NULL CHECK(office IN ('morning', 'evening')),
    completed_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_completions_user_date_office
    ON completions(COALESCE(user_id, ''), date, office);
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_CREATE_SQL)
        await db.commit()


async def mark_complete(date: str, office: str, user_id: Optional[str] = None) -> bool:
    """Mark an office complete. Returns True if newly inserted, False if already existed."""
    now = datetime.datetime.now().isoformat(timespec="seconds")
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO completions (user_id, date, office, completed_at) VALUES (?, ?, ?, ?)",
                (user_id, date, office, now),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def unmark(date: str, office: str, user_id: Optional[str] = None) -> bool:
    """Unmark a completion. Returns True if deleted, False if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM completions WHERE COALESCE(user_id, '') = ? AND date = ? AND office = ?",
            (user_id or "", date, office),
        )
        await db.commit()
        return cursor.rowcount > 0


async def is_complete(date: str, office: str, user_id: Optional[str] = None) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM completions WHERE COALESCE(user_id, '') = ? AND date = ? AND office = ?",
            (user_id or "", date, office),
        )
        return await cursor.fetchone() is not None


async def get_completions(
    from_date: str, to_date: str, user_id: Optional[str] = None
) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT date, office, completed_at FROM completions "
            "WHERE COALESCE(user_id, '') = ? AND date BETWEEN ? AND ? "
            "ORDER BY date DESC, office",
            (user_id or "", from_date, to_date),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
