"""GET /api/office/{date}/full — Complete Morning and Evening Prayer service."""
import re
from datetime import date as DateType

from fastapi import APIRouter, HTTPException, Path, Query

from app.bible.db import fetch_psalm, fetch_verses
from app.office.builder import build_office

router = APIRouter(prefix="/api/office", tags=["office-full"])

_PLAIN_RE = re.compile(r"^\d+$")
_BRACKETED_RE = re.compile(r"^\[(\d+)\]$")


async def _expand_psalm_token(token: str) -> dict:
    """Expand one psalm token (plain, bracketed, or verse-ranged) to a psalm block."""
    token = token.strip()

    m = _BRACKETED_RE.match(token)
    if m:
        n = int(m.group(1))
        raw = await fetch_psalm(n)
        return {"type": "psalm", "number": n, "optional": True,
                "verses": [{"verse": v["verse"], "text": v["text"]} for v in raw]}

    if _PLAIN_RE.match(token):
        n = int(token)
        raw = await fetch_psalm(n)
        return {"type": "psalm", "number": n, "optional": False,
                "verses": [{"verse": v["verse"], "text": v["text"]} for v in raw]}

    # Verse range like "119:1-24"
    n = int(token.split(":")[0])
    raw = await fetch_verses(f"Ps {token}")
    return {"type": "psalm", "number": n, "optional": False,
            "token": token,
            "verses": [{"verse": v["verse"], "text": v["text"]} for v in raw]}


async def _expand_blocks(blocks: list[dict]) -> list[dict]:
    """Replace psalm_ref and lesson_ref placeholder blocks with hydrated verse text."""
    expanded = []
    for block in blocks:
        if block["type"] == "psalm_ref":
            psalm_block = await _expand_psalm_token(block["token"])
            expanded.append(psalm_block)

        elif block["type"] == "lesson_ref":
            ref = block["reference"]
            try:
                raw = await fetch_verses(ref)
                verses = [{"book": v["book"], "chapter": v["chapter"],
                           "verse": v["verse"], "text": v["text"]} for v in raw]
            except Exception:
                verses = []
            expanded.append({
                "type": "lesson",
                "position": block["position"],
                "reference": ref,
                "verses": verses,
            })

        else:
            expanded.append(block)

    return expanded


@router.get(
    "/{office_date}/full",
    summary="Full Daily Office service for a date",
    description="""
Return the complete BCP 1979 Rite II Morning and Evening Prayer service as an
ordered list of liturgical blocks for a given date.

Each block has a `type` field:
- `heading` — section heading
- `rubric` — italic liturgical instruction
- `sentence` — opening sentence with scripture reference
- `confession` — Confession of Sin (invitation, text, absolution)
- `versicle` — one or more leader/response pairs
- `canticle` — canticle with name, source, and verse lines
- `psalm` — psalm with full verse text
- `lesson` — scripture lesson with full verse text
- `text` — prose prayer or creed
- `collect` — collect with contemporary and optional traditional text
- `suffrages` — suffrages A or B as versicle pairs

Pass `?suffrages=B` to use Suffrages B instead of A (default).
""",
    responses={
        404: {"description": "No lectionary entry for the given date"},
        422: {"description": "Invalid date format"},
    },
)
async def get_office_full(
    office_date: str = Path(
        ...,
        description="Calendar date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        examples=["2026-05-27"],
    ),
    suffrages: str = Query("A", pattern="^[ABab]$",
                           description="Suffrages form: A or B"),
) -> dict:
    try:
        d = DateType.fromisoformat(office_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format; use YYYY-MM-DD")

    morning_raw = build_office(d, "morning", suffrages.upper())
    evening_raw = build_office(d, "evening", suffrages.upper())

    # Check that we actually have lectionary data (builder returns blocks regardless,
    # but lessons/psalms will be empty if resolve_office returned None)
    morning_blocks = await _expand_blocks(morning_raw)
    evening_blocks = await _expand_blocks(evening_raw)

    return {
        "date": office_date,
        "suffrages_form": suffrages.upper(),
        "morning": morning_blocks,
        "evening": evening_blocks,
    }
