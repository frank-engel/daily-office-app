"""GET /api/bible/{reference} — fetch verse text for any lectionary reference."""
from fastapi import APIRouter, HTTPException

from app.bible.db import fetch_verses
from app.schemas import BibleResponse, VerseResponse

router = APIRouter(prefix="/api/bible", tags=["bible"])


@router.get(
    "/{reference:path}",
    response_model=BibleResponse,
    summary="Verse text for a Bible reference",
    description="""
Return verse text for any BCP lectionary Bible reference string.

Supported formats (both ASCII hyphen `-` and en-dash `–` are accepted):

| Format | Example |
|--------|---------|
| Simple range | `Isa 1:1-9` |
| Multi-range, same chapter | `Isa 5:8-12, 18-23` |
| Semicolon-separated sections | `Gal 3:23-29; 4:4-7` |
| Letter-suffixed verse | `2 Pet 2:1-10a` |
| Cross-chapter range | `Luke 20:41-21:4` |
| Parenthetical optional suffix | `John 17:1-11(12-26)` |
| Parenthetical optional prefix | `Isa 42:(1-9)10-17` |

Apocryphal books (Sir, Wis, Tob, Jdt, Bar, 1–2 Macc, 1–2 Esd) are supported.
Text source: King James Version with Apocrypha (KJVA).
""",
    responses={
        404: {"description": "Reference could not be parsed or no verses matched"},
    },
)
async def get_bible(reference: str) -> BibleResponse:
    raw = await fetch_verses(reference)
    if not raw:
        raise HTTPException(status_code=404, detail=f"No verses found for: {reference!r}")
    verses = [VerseResponse(**v) for v in raw]
    return BibleResponse(reference=reference, verses=verses)
