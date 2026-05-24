"""GET /api/psalms/{numbers} — fetch one or more complete psalms by number."""
from fastapi import APIRouter, HTTPException, Path

from app.bible.db import fetch_psalm
from app.schemas import PsalmEntry, PsalmVerseResponse

router = APIRouter(prefix="/api/psalms", tags=["psalms"])


@router.get(
    "/{numbers}",
    response_model=dict[str, PsalmEntry],
    summary="Full text of one or more psalms",
    description="""
Return every verse of one or more psalms by number.

Pass a single number (`23`) or a comma-separated list (`146,147`).
The response is a dict keyed by psalm number string, each value containing the
psalm number and its ordered verse list.

Psalm text source: King James Version with Apocrypha (KJVA).
""",
    responses={
        422: {"description": "Non-numeric or missing psalm numbers"},
    },
)
async def get_psalms(
    numbers: str = Path(
        ...,
        description="Comma-separated psalm number(s), e.g. `23` or `146,147`",
        examples=["23", "146,147"],
    ),
) -> dict[str, PsalmEntry]:
    parts = [p.strip() for p in numbers.split(",") if p.strip()]
    if not parts:
        raise HTTPException(status_code=422, detail="No psalm numbers provided")

    result: dict[str, PsalmEntry] = {}
    for part in parts:
        try:
            n = int(part)
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid psalm number: {part!r}")
        raw = await fetch_psalm(n)
        verses = [PsalmVerseResponse(**v) for v in raw]
        result[str(n)] = PsalmEntry(psalm=n, verses=verses)

    return result
