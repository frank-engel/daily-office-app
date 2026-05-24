"""GET /api/office/{date} — Daily Office lectionary with full verse text."""
import re
from datetime import date as DateType

from fastapi import APIRouter, HTTPException, Path

from app.bible.db import fetch_psalm, fetch_verses
from app.lectionary.resolver import resolve_office
from app.schemas import LessonEntry, OfficeResponse, PsalmEntry, PsalmVerseResponse, VerseResponse

router = APIRouter(prefix="/api/office", tags=["office"])

# Psalm numbers in the lectionary JSON come in three forms:
#   "23"            — plain integer, fetch whole psalm
#   "[58]"          — bracketed optional, strip brackets, fetch whole psalm
#   "119:1–24"      — verse range, fetch via reference parser
#   "21:1–7(8–14)"  — verse range with optional extension
_PLAIN_RE = re.compile(r"^\d+$")
_BRACKETED_RE = re.compile(r"^\[(\d+)\]$")


async def _expand_psalm_token(token: str) -> PsalmEntry:
    """Resolve one psalm token (possibly bracketed or verse-ranged) to a PsalmEntry."""
    token = token.strip()

    # "[n]" — optional psalm; strip brackets and treat as whole psalm
    m = _BRACKETED_RE.match(token)
    if m:
        n = int(m.group(1))
        raw = await fetch_psalm(n)
        return PsalmEntry(psalm=n, verses=[PsalmVerseResponse(**v) for v in raw])

    # Plain integer — whole psalm
    if _PLAIN_RE.match(token):
        n = int(token)
        raw = await fetch_psalm(n)
        return PsalmEntry(psalm=n, verses=[PsalmVerseResponse(**v) for v in raw])

    # Verse range like "119:1–24" or "21:1–7(8–14)" — use reference parser
    # The psalm number is the part before the colon.
    n = int(token.split(":")[0])
    raw = await fetch_verses(f"Ps {token}")
    # fetch_verses returns {book, chapter, verse, text}; adapt to PsalmVerseResponse
    verses = [PsalmVerseResponse(psalm=n, verse=v["verse"], text=v["text"]) for v in raw]
    return PsalmEntry(psalm=n, verses=verses)


async def _expand_psalms(psalm_numbers: list[str]) -> list[PsalmEntry]:
    return [await _expand_psalm_token(t) for t in psalm_numbers]


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


async def build_office_context(office_date: str) -> dict | None:
    """Fetch and expand full office data for a date string. Returns None if not found."""
    try:
        d = DateType.fromisoformat(office_date)
    except ValueError:
        return None
    result = resolve_office(d)
    if result is None:
        return None
    return {
        "date": result["date"],
        "title": result.get("title"),
        "season": result["season"],
        "week": result["week"],
        "cycle": result["cycle"],
        "morning_psalms": await _expand_psalms(result["psalms"]["morning"]),
        "evening_psalms": await _expand_psalms(result["psalms"]["evening"]),
        "morning_lessons": await _expand_lessons(result["morning_lessons"]),
        "evening_lessons": await _expand_lessons(result["evening_lessons"]),
    }


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
        DateType.fromisoformat(office_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format; use YYYY-MM-DD")

    ctx = await build_office_context(office_date)
    if ctx is None:
        raise HTTPException(
            status_code=404,
            detail=f"No lectionary entry found for {office_date}",
        )

    return OfficeResponse(
        date=ctx["date"],
        title=ctx["title"],
        season=ctx["season"],
        week=ctx["week"],
        cycle=ctx["cycle"],
        psalms={"morning": ctx["morning_psalms"], "evening": ctx["evening_psalms"]},
        morning_lessons=ctx["morning_lessons"],
        evening_lessons=ctx["evening_lessons"],
        reflection=None,
    )
