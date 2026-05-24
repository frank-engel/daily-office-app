"""
GET /api/office/{date}

Returns the Daily Office lectionary for a given date.
Phase 2: lectionary references only — no Bible verse text yet (Phase 3).
"""
from datetime import date as DateType

from fastapi import APIRouter, HTTPException, Path

from app.lectionary.resolver import resolve_office

router = APIRouter(prefix="/api/office", tags=["office"])


@router.get("/{office_date}")
async def get_office(
    office_date: str = Path(
        ..., description="Date in YYYY-MM-DD format", pattern=r"^\d{4}-\d{2}-\d{2}$"
    ),
):
    try:
        d = DateType.fromisoformat(office_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format; use YYYY-MM-DD")

    result = resolve_office(d)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No lectionary entry found for {office_date}",
        )
    return result
