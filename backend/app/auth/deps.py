"""FastAPI dependencies for authentication."""

from fastapi import Depends, HTTPException, Request

from app.auth.db import User, get_user_by_id


async def get_current_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await get_user_by_id(user_id)


async def require_user_api(user: User | None = Depends(get_current_user)) -> User:
    """For JSON API routes: returns 401 if not authenticated."""
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
