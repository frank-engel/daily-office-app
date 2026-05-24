"""
Integration tests for bible/db.py — hit the real web.sqlite.

Skipped automatically if web.sqlite is absent so CI doesn't break.
"""
import pytest
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "web.sqlite"
pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="web.sqlite not present"
)

from app.bible.db import fetch_verses, fetch_psalm, startup_check


@pytest.mark.asyncio
async def test_startup_check_runs():
    # Should complete without raising
    await startup_check()


@pytest.mark.asyncio
async def test_fetch_psalm_23():
    verses = await fetch_psalm(23)
    assert len(verses) == 6
    assert verses[0]["verse"] == 1
    assert "shepherd" in verses[0]["text"].lower()


@pytest.mark.asyncio
async def test_fetch_psalm_119_first_verse():
    verses = await fetch_psalm(119)
    assert verses[0]["verse"] == 1
    assert len(verses) > 100  # Psalm 119 has 176 verses


@pytest.mark.asyncio
async def test_fetch_verses_simple_range():
    verses = await fetch_verses("Isa 1:1–9")
    assert len(verses) == 9
    assert verses[0]["chapter"] == 1
    assert verses[0]["verse"] == 1


@pytest.mark.asyncio
async def test_fetch_verses_cross_chapter():
    verses = await fetch_verses("Luke 20:41–21:4")
    chapters = {v["chapter"] for v in verses}
    assert 20 in chapters
    assert 21 in chapters


@pytest.mark.asyncio
async def test_fetch_verses_sirach():
    verses = await fetch_verses("Sir 1:1–5")
    assert len(verses) == 5
    assert "wisdom" in verses[0]["text"].lower()


@pytest.mark.asyncio
async def test_fetch_verses_wisdom():
    verses = await fetch_verses("Wis 1:1–5")
    assert len(verses) >= 1


@pytest.mark.asyncio
async def test_fetch_verses_multi_range():
    verses = await fetch_verses("Isa 5:8–12, 18–23")
    verse_nums = [v["verse"] for v in verses]
    assert 8 in verse_nums
    assert 12 in verse_nums
    assert 18 in verse_nums
    assert 23 in verse_nums
    # verses 13–17 should NOT be present
    assert 13 not in verse_nums


@pytest.mark.asyncio
async def test_fetch_verses_semicolon_separated():
    verses = await fetch_verses("Gal 3:23–29; 4:4–7")
    chapters = [v["chapter"] for v in verses]
    assert 3 in chapters
    assert 4 in chapters


@pytest.mark.asyncio
async def test_fetch_verses_parenthetical_stripped():
    # John 17:1–11(12–26) should return only verses 1-11
    verses = await fetch_verses("John 17:1–11(12–26)")
    assert all(v["verse"] <= 11 for v in verses)
    assert len(verses) == 11
