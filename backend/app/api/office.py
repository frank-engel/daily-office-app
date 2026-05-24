"""GET /api/office/{date} — Daily Office lectionary with full verse text."""
from datetime import date as DateType

from fastapi import APIRouter, HTTPException, Path

from app.bible.db import fetch_psalm, fetch_verses
from app.lectionary.resolver import resolve_office
from app.schemas import LessonEntry, OfficeResponse, PsalmEntry, PsalmVerseResponse, VerseResponse

router = APIRouter(prefix="/api/office", tags=["office"])


async def _expand_lessons(lessons: dict) -> dict[str, LessonEntry]:
    expanded = {}
    for key, ref in lessons.items():
        if ref:
            raw = await fetch_verses(ref)
            verses = [VerseResponse(**v) for v in raw]
            expanded[key] = LessonEntry(reference=ref, verses=verses)
        else:
            expanded[key] = LessonEntry(reference=None, verses=[])
    return expanded


async def _expand_psalms(psalm_numbers: list[str]) -> list[PsalmEntry]:
    result = []
    for num in psalm_numbers:
        raw = await fetch_psalm(num)
        verses = [PsalmVerseResponse(**v) for v in raw]
        result.append(PsalmEntry(psalm=int(num), verses=verses))
    return result


@router.get(
    "/{office_date}",
    response_model=OfficeResponse,
    summary="Daily Office for a date",
    description="""
Return the complete BCP 1979 Daily Office lectionary for the given date, including:

- Liturgical season, week name, and year-cycle (1 or 2)
- Psalm assignments for Morning and Evening Prayer, with full verse text
- Scripture lesson assignments for Morning and Evening Prayer, with full verse text
- The feast or Sunday title if applicable

Verse text is drawn from the King James Version with Apocrypha (KJVA).
Apocryphal readings required by the Anglican lectionary (Sirach, Wisdom, etc.) are fully supported.

**Date arithmetic** follows the BCP 1979 calendar engine:
Easter is computed by the Gregorian Computus algorithm; Advent, Pentecost, and all
moveable feasts are derived from it.
""",
    responses={
        404: {"description": "No lectionary entry found for the given date (e.g. a Season-after-Pentecost weekday with no assigned readings)"},
        422: {"description": "Invalid date format"},
    },
)
async def get_office(
    office_date: str = Path(
        ...,
        description="Calendar date in **YYYY-MM-DD** format",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        examples=["2026-05-24", "2024-12-01"],
    ),
) -> OfficeResponse:
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

    morning_psalms = await _expand_psalms(result["psalms"]["morning"])
    evening_psalms = await _expand_psalms(result["psalms"]["evening"])
    morning_lessons = await _expand_lessons(result["morning_lessons"])
    evening_lessons = await _expand_lessons(result["evening_lessons"])

    return OfficeResponse(
        date=result["date"],
        title=result.get("title"),
        season=result["season"],
        week=result["week"],
        cycle=result["cycle"],
        psalms={"morning": morning_psalms, "evening": evening_psalms},
        morning_lessons=morning_lessons,
        evening_lessons=evening_lessons,
        reflection=None,
    )
