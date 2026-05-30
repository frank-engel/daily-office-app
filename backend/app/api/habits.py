"""GET /api/habits  POST /api/habits/{date}/{office}  DELETE /api/habits/{date}/{office}"""
import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.auth.db import User
from app.auth.deps import require_user_api
from app.habits.db import get_completions, mark_complete, unmark

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("", summary="List completions for a date range")
async def list_habits(
    from_date: str | None = None,
    to_date: str | None = None,
    user: User = Depends(require_user_api),
):
    """Return all completions between `from_date` and `to_date` (defaults: last 30 days)."""
    today = datetime.date.today()
    if to_date is None:
        to_date = today.isoformat()
    if from_date is None:
        from_date = (today - datetime.timedelta(days=29)).isoformat()
    rows = await get_completions(from_date, to_date, user_id=user.id)
    return {"from": from_date, "to": to_date, "completions": rows}


@router.post("/{date}/{office}", summary="Mark an office complete", status_code=201)
async def complete_office(
    date: str,
    office: str,
    user: User = Depends(require_user_api),
):
    if office not in ("morning", "evening"):
        return JSONResponse({"error": "office must be 'morning' or 'evening'"}, status_code=422)
    created = await mark_complete(date, office, user_id=user.id)
    return JSONResponse(
        {"date": date, "office": office, "completed": True},
        status_code=201 if created else 200,
    )


@router.delete("/{date}/{office}", summary="Unmark an office completion", status_code=204)
async def uncomplete_office(
    date: str,
    office: str,
    user: User = Depends(require_user_api),
):
    if office not in ("morning", "evening"):
        return JSONResponse({"error": "office must be 'morning' or 'evening'"}, status_code=422)
    await unmark(date, office, user_id=user.id)
    return JSONResponse(None, status_code=204)
