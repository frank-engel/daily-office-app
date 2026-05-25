"""GET /api/habits  POST /api/habits/{date}/{office}  DELETE /api/habits/{date}/{office}"""
import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.habits.db import get_completions, mark_complete, unmark

router = APIRouter(prefix="/api/habits", tags=["habits"])


@router.get("", summary="List completions for a date range")
async def list_habits(
    from_date: str | None = None,
    to_date: str | None = None,
):
    """Return all completions between `from_date` and `to_date` (defaults: last 30 days)."""
    today = datetime.date.today()
    if to_date is None:
        to_date = today.isoformat()
    if from_date is None:
        from_date = (today - datetime.timedelta(days=29)).isoformat()
    rows = await get_completions(from_date, to_date)
    return {"from": from_date, "to": to_date, "completions": rows}


@router.post("/{date}/{office}", summary="Mark an office complete", status_code=201)
async def complete_office(date: str, office: str):
    if office not in ("morning", "evening"):
        return JSONResponse({"error": "office must be 'morning' or 'evening'"}, status_code=422)
    created = await mark_complete(date, office)
    return JSONResponse(
        {"date": date, "office": office, "completed": True},
        status_code=201 if created else 200,
    )


@router.delete("/{date}/{office}", summary="Unmark an office completion", status_code=204)
async def uncomplete_office(date: str, office: str):
    if office not in ("morning", "evening"):
        return JSONResponse({"error": "office must be 'morning' or 'evening'"}, status_code=422)
    await unmark(date, office)
    return JSONResponse(None, status_code=204)
