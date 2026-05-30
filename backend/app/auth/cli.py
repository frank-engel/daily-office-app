"""Admin CLI for user management.

Usage (run from backend/ with venv active):

  # Invite a tester — creates account, prints set-password URL
  python -m app.auth.cli invite tester@example.com
  python -m app.auth.cli invite tester@example.com --name "Jane Smith"

  # Reset a user's password (sets a temporary password they should change)
  python -m app.auth.cli reset-password user@example.com newpassword123

  # List all users
  python -m app.auth.cli list-users
"""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()

from app.auth.db import (
    create_invited_user,
    get_user_by_email,
    init_db,
    set_user_password,
    count_users,
    get_user_by_id,
)
from app.auth.tokens import create_invite_token
import aiosqlite
import os


async def cmd_invite(email: str, name: str | None) -> None:
    await init_db()
    existing = await get_user_by_email(email)
    if existing is not None:
        user, pw_hash = existing
        if pw_hash is not None:
            print(f"ERROR: {email} already has an account with a password set.")
            sys.exit(1)
        else:
            # Already invited but hasn't set password — regenerate token
            print(f"NOTE: {email} was already invited. Generating a new link.")
            user_id = user.id
    else:
        user = await create_invited_user(email, display_name=name)
        user_id = user.id
        print(f"Created account for: {email}")

    token = create_invite_token(user_id)
    print(f"\nShare this set-password link with {email}:")
    print(f"  /set-password?token={token}")
    print("\n(Prepend your domain, e.g. https://office.yourdomain.com/set-password?token=...)")
    print("Link expires in 48 hours.")


async def cmd_reset_password(email: str, new_password: str) -> None:
    await init_db()
    result = await get_user_by_email(email)
    if result is None:
        print(f"ERROR: No account found for {email}")
        sys.exit(1)
    user, _ = result
    await set_user_password(user.id, new_password)
    print(f"Password reset for {email}.")


async def cmd_list_users() -> None:
    await init_db()
    db_path = os.getenv("USERS_DB_PATH", "data/users.sqlite")
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await (await db.execute(
            "SELECT email, display_name, password_hash IS NULL AS pending, created_at FROM users ORDER BY created_at"
        )).fetchall()
    if not rows:
        print("No users.")
        return
    print(f"{'Email':<35} {'Name':<20} {'Status':<12} {'Created'}")
    print("-" * 85)
    for r in rows:
        status = "pending" if r["pending"] else "active"
        name = r["display_name"] or ""
        print(f"{r['email']:<35} {name:<20} {status:<12} {r['created_at'][:19]}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "invite":
        if len(sys.argv) < 3:
            print("Usage: python -m app.auth.cli invite EMAIL [--name NAME]")
            sys.exit(1)
        email = sys.argv[2]
        name = None
        if "--name" in sys.argv:
            idx = sys.argv.index("--name")
            if idx + 1 < len(sys.argv):
                name = sys.argv[idx + 1]
        asyncio.run(cmd_invite(email, name))

    elif command == "reset-password":
        if len(sys.argv) < 4:
            print("Usage: python -m app.auth.cli reset-password EMAIL NEW_PASSWORD")
            sys.exit(1)
        asyncio.run(cmd_reset_password(sys.argv[2], sys.argv[3]))

    elif command == "list-users":
        asyncio.run(cmd_list_users())

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
