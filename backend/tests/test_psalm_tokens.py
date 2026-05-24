"""
Tests for _expand_psalm_token — the three lectionary psalm formats.

Skipped when web.sqlite is absent so CI works without the database.
"""
import pytest
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "web.sqlite"
pytestmark = pytest.mark.skipif(
    not DB_PATH.exists(), reason="web.sqlite not present"
)

from app.api.office import _expand_psalm_token
from app.schemas import PsalmEntry


@pytest.mark.asyncio
async def test_plain_integer():
    entry = await _expand_psalm_token("23")
    assert isinstance(entry, PsalmEntry)
    assert entry.psalm == 23
    assert len(entry.verses) == 6
    assert "shepherd" in entry.verses[0].text.lower()


@pytest.mark.asyncio
async def test_bracketed_optional():
    # "[58]" — optional psalm, square brackets stripped
    entry = await _expand_psalm_token("[58]")
    assert isinstance(entry, PsalmEntry)
    assert entry.psalm == 58
    assert len(entry.verses) > 0


@pytest.mark.asyncio
async def test_verse_range():
    # "119:1–24" — verse range, en-dash separator
    entry = await _expand_psalm_token("119:1–24")
    assert isinstance(entry, PsalmEntry)
    assert entry.psalm == 119
    assert len(entry.verses) == 24
    assert entry.verses[0].verse == 1
    assert entry.verses[-1].verse == 24


@pytest.mark.asyncio
async def test_verse_range_with_optional_extension():
    # "21:1–7(8–14)" — range with parenthetical extension (stripped)
    entry = await _expand_psalm_token("21:1–7(8–14)")
    assert isinstance(entry, PsalmEntry)
    assert entry.psalm == 21
    # Parenthetical stripped by reference parser — expect verses 1–7
    assert entry.verses[0].verse == 1
    assert entry.verses[-1].verse == 7


@pytest.mark.asyncio
async def test_christmas_evening_psalm():
    # The real problematic token from the Christmas entry
    entry = await _expand_psalm_token("110:1–5(6–7)")
    assert entry.psalm == 110
    assert entry.verses[0].verse == 1
    assert entry.verses[-1].verse == 5
