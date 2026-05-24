"""
Async SQLite verse lookup against web.sqlite (KJVA_books / KJVA_verses tables).

Public API:
  startup_check()  — call once at app startup; logs warnings for missing apoc books
  fetch_verses(ref_str)  → list[dict]  — parse ref, fetch verses
  fetch_psalm(number)    → list[dict]  — fetch all verses of a psalm
"""
from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from .book_map import book_id
from .reference_parser import parse_reference, VerseRange

log = logging.getLogger(__name__)

_DB_PATH = Path(__file__).parent.parent.parent / "data" / "web.sqlite"

# Apocryphal books the BCP lectionary references
_REQUIRED_APOCRYPHA = {
    "Sir": "Sirach",
    "Wis": "Wisdom",
    "1 Macc": "I Maccabees",
    "Jdt": "Judith",
    "Bar": "Baruch",
    "Tob": "Tobit",
    "2 Esd": "II Esdras",
}

_MISSING_TEXT = "[Text not available in this edition]"


async def startup_check() -> None:
    """Verify DB exists and Apocryphal books are present; log warnings for any missing."""
    if not _DB_PATH.exists():
        log.error("web.sqlite not found at %s — Bible text unavailable", _DB_PATH)
        return

    async with aiosqlite.connect(_DB_PATH) as db:
        for abbrev, full_name in _REQUIRED_APOCRYPHA.items():
            bid = book_id(abbrev)
            if bid is None:
                log.warning("No book_id mapping for %s (%s)", abbrev, full_name)
                continue
            async with db.execute(
                "SELECT COUNT(*) FROM KJVA_books WHERE id = ?", (bid,)
            ) as cur:
                row = await cur.fetchone()
                if not row or row[0] == 0:
                    log.warning("Apocryphal book missing from DB: %s (%s)", abbrev, full_name)
                else:
                    log.debug("Apocryphal book present: %s (id=%d)", abbrev, bid)


async def _fetch_range(db: aiosqlite.Connection, vr: VerseRange) -> list[dict]:
    """Fetch all verses for a single VerseRange."""
    bid = book_id(vr.book)
    if bid is None:
        log.warning("Unknown book abbreviation: %s", vr.book)
        return [{"book": vr.book, "chapter": vr.start_chapter, "verse": vr.start_verse,
                 "text": _MISSING_TEXT}]

    # Build WHERE clause for the range
    if vr.start_chapter == vr.end_chapter:
        sql = """
            SELECT chapter, verse, text
            FROM KJVA_verses
            WHERE book_id = ? AND chapter = ? AND verse BETWEEN ? AND ?
            ORDER BY chapter, verse
        """
        params = (bid, vr.start_chapter, vr.start_verse, vr.end_verse)
    else:
        # Cross-chapter range
        sql = """
            SELECT chapter, verse, text
            FROM KJVA_verses
            WHERE book_id = ?
              AND (
                (chapter = ? AND verse >= ?)
                OR (chapter > ? AND chapter < ?)
                OR (chapter = ? AND verse <= ?)
              )
            ORDER BY chapter, verse
        """
        params = (
            bid,
            vr.start_chapter, vr.start_verse,
            vr.start_chapter, vr.end_chapter,
            vr.end_chapter, vr.end_verse,
        )

    rows = []
    async with db.execute(sql, params) as cur:
        async for row in cur:
            rows.append({"book": vr.book, "chapter": row[0], "verse": row[1], "text": row[2]})

    if not rows:
        log.warning("No verses found for %s %d:%d–%d:%d",
                    vr.book, vr.start_chapter, vr.start_verse, vr.end_chapter, vr.end_verse)
        rows.append({"book": vr.book, "chapter": vr.start_chapter, "verse": vr.start_verse,
                     "text": _MISSING_TEXT})
    return rows


async def fetch_verses(ref_str: str) -> list[dict]:
    """
    Parse *ref_str* and return all matching verses as a list of dicts.

    Each dict: {"book": str, "chapter": int, "verse": int, "text": str}
    Returns a single-element list with the missing-text sentinel on failure.
    """
    if not ref_str or not ref_str.strip():
        return []

    ranges = parse_reference(ref_str)
    if not ranges:
        log.warning("Could not parse reference: %r", ref_str)
        return [{"book": "", "chapter": 0, "verse": 0, "text": _MISSING_TEXT}]

    async with aiosqlite.connect(_DB_PATH) as db:
        results: list[dict] = []
        for vr in ranges:
            results.extend(await _fetch_range(db, vr))
    return results


async def fetch_psalm(number: int | str) -> list[dict]:
    """Fetch all verses of a psalm by number."""
    n = int(number)
    bid = book_id("Ps")
    if bid is None:
        return []

    async with aiosqlite.connect(_DB_PATH) as db:
        rows = []
        async with db.execute(
            "SELECT chapter, verse, text FROM KJVA_verses WHERE book_id = ? AND chapter = ? ORDER BY verse",
            (bid, n),
        ) as cur:
            async for row in cur:
                rows.append({"psalm": n, "verse": row[1], "text": row[2]})
    return rows
