"""User account storage: users.sqlite with versioned migrations."""

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import bcrypt as _bcrypt
import aiosqlite

_DB_PATH = os.getenv("USERS_DB_PATH", "data/users.sqlite")

# Each tuple: (version, sql). Applied in order at startup if not yet run.
_MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            email         TEXT UNIQUE NOT NULL,
            display_name  TEXT,
            password_hash TEXT NOT NULL,
            timezone      TEXT NOT NULL DEFAULT 'UTC',
            collect_style TEXT NOT NULL DEFAULT 'contemporary',
            created_at    TEXT NOT NULL
        )
        """,
    ),
]


@dataclass
class User:
    id: str
    email: str
    display_name: str | None
    timezone: str
    collect_style: str


async def init_db() -> None:
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"""
        )
        row = await db.execute("SELECT MAX(version) FROM schema_version")
        current = (await row.fetchone())[0] or 0
        for version, sql in _MIGRATIONS:
            if version > current:
                await db.executescript(sql)
                await db.execute(
                    "INSERT OR IGNORE INTO schema_version VALUES (?)", (version,)
                )
        await db.commit()


async def create_user(email: str, password: str, display_name: str | None = None) -> User:
    user_id = str(uuid.uuid4())
    password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt(rounds=12)).decode()
    created_at = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (id, email, display_name, password_hash, timezone, collect_style, created_at)
               VALUES (?, ?, ?, ?, 'UTC', 'contemporary', ?)""",
            (user_id, email.lower().strip(), display_name, password_hash, created_at),
        )
        await db.commit()
    return User(
        id=user_id,
        email=email.lower().strip(),
        display_name=display_name,
        timezone="UTC",
        collect_style="contemporary",
    )


async def get_user_by_id(user_id: str) -> User | None:
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute(
            "SELECT id, email, display_name, timezone, collect_style FROM users WHERE id = ?",
            (user_id,),
        )
        r = await row.fetchone()
    if not r:
        return None
    return User(
        id=r["id"],
        email=r["email"],
        display_name=r["display_name"],
        timezone=r["timezone"],
        collect_style=r["collect_style"],
    )


async def get_user_by_email(email: str) -> tuple[User, str] | None:
    """Returns (User, password_hash) or None."""
    async with aiosqlite.connect(_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute(
            "SELECT id, email, display_name, timezone, collect_style, password_hash FROM users WHERE email = ?",
            (email.lower().strip(),),
        )
        r = await row.fetchone()
    if not r:
        return None
    return (
        User(
            id=r["id"],
            email=r["email"],
            display_name=r["display_name"],
            timezone=r["timezone"],
            collect_style=r["collect_style"],
        ),
        r["password_hash"],
    )


async def count_users() -> int:
    async with aiosqlite.connect(_DB_PATH) as db:
        row = await db.execute("SELECT COUNT(*) FROM users")
        return (await row.fetchone())[0]


async def update_preferences(user_id: str, timezone: str, collect_style: str, display_name: str | None) -> None:
    async with aiosqlite.connect(_DB_PATH) as db:
        await db.execute(
            """UPDATE users SET timezone = ?, collect_style = ?, display_name = ? WHERE id = ?""",
            (timezone, collect_style, display_name, user_id),
        )
        await db.commit()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())
