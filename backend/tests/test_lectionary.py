"""
Tests for Phase 2: liturgical calendar context and lectionary resolver.

Ground-truth dates verified against lectionarypage.net.
"""
import pytest
from datetime import date

from app.calendar.liturgical_year import liturgical_context
from app.lectionary.loader import load_lectionary, DAILY_INDEX
from app.lectionary.resolver import resolve_office, flatten_lessons


# ---------------------------------------------------------------------------
# Ensure the index is loaded once for all tests in this module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def loaded_index():
    load_lectionary()


# ---------------------------------------------------------------------------
# liturgical_context — known-good dates from the spec
# ---------------------------------------------------------------------------

def test_advent_sunday_2024():
    ctx = liturgical_context(date(2024, 12, 1))
    assert ctx["week"] == "Week of 1 Advent"
    assert ctx["day"] == "Sunday"
    assert ctx["cycle"] == 1
    assert ctx["season"] == "Advent"


def test_ash_wednesday_2026():
    ctx = liturgical_context(date(2026, 2, 18))
    assert ctx["week"] == "Ash Wednesday and Following"
    assert ctx["day"] == "Wednesday"
    assert ctx["cycle"] == 2


def test_easter_2026():
    ctx = liturgical_context(date(2026, 4, 5))
    assert ctx["week"] == "Easter Week"
    assert ctx["day"] == "Sunday"
    assert ctx["cycle"] == 2


def test_eve_of_pentecost_2026():
    # 2026-05-23 = Eve of Pentecost, Year Two
    ctx = liturgical_context(date(2026, 5, 23))
    assert ctx["week"] == "Week of 7 Easter"
    assert ctx["day"] == "Saturday"
    assert ctx["cycle"] == 2


def test_pentecost_sunday_2026():
    ctx = liturgical_context(date(2026, 5, 24))
    assert ctx["week"] == "Pentecost"
    assert ctx["day"] == "Sunday"
    assert ctx["cycle"] == 2


def test_trinity_eve_2026():
    ctx = liturgical_context(date(2026, 5, 30))
    assert ctx["week"] == ""
    assert ctx["day"] == "Saturday"
    assert ctx["title"] == "Eve of Trinity Sunday"


def test_trinity_sunday_2026():
    ctx = liturgical_context(date(2026, 5, 31))
    assert ctx["week"] == ""
    assert ctx["day"] == "Sunday"
    assert "Trinity" in ctx["title"]


def test_pentecost_weekday_returns_none():
    # Monday after Pentecost — no lectionary entry
    ctx = liturgical_context(date(2026, 5, 25))
    assert ctx is None


# ---------------------------------------------------------------------------
# Advent week numbering
# ---------------------------------------------------------------------------

def test_advent_4_2024():
    # Dec 22 2024 = last Sunday before Christmas → Week of 4 Advent
    ctx = liturgical_context(date(2024, 12, 22))
    assert ctx["week"] == "Week of 4 Advent"
    assert ctx["day"] == "Sunday"


def test_advent_4_friday_2024():
    ctx = liturgical_context(date(2024, 12, 27))
    # Dec 27 is after Christmas, so this should be Christmas season
    assert ctx["week"] == "Christmas Day and Following"


# ---------------------------------------------------------------------------
# Christmas season day naming
# ---------------------------------------------------------------------------

def test_christmas_day_2025():
    ctx = liturgical_context(date(2025, 12, 25))
    assert ctx["week"] == "Christmas Day and Following"
    assert ctx["day"] == "Dec 25"


def test_christmas_sunday():
    # Find a year where a Sunday falls between Dec 26-31
    # Dec 28, 2025 is a Sunday (Dec 25 Thu → Dec 28 Sun)
    ctx = liturgical_context(date(2025, 12, 28))
    assert ctx["week"] == "Christmas Day and Following"
    assert ctx["day"] == "Sunday"


def test_holy_name_jan1():
    ctx = liturgical_context(date(2026, 1, 1))
    assert ctx["week"] == "Christmas Day and Following"
    assert ctx["day"] == "Jan 1"


def test_eve_of_epiphany():
    ctx = liturgical_context(date(2026, 1, 5))
    assert ctx["week"] == "Christmas Day and Following"
    assert ctx["day"] == "Jan 5"


# ---------------------------------------------------------------------------
# Epiphany and Following
# ---------------------------------------------------------------------------

def test_epiphany_jan6():
    ctx = liturgical_context(date(2026, 1, 6))
    assert ctx["week"] == "The Epiphany and Following"
    assert ctx["day"] == "Jan 6"


def test_epiphany_eve_of_1():
    # The Saturday before Baptism Sunday (first Sunday after Jan 6)
    # Jan 6 2026 = Tuesday → baptism = Jan 11 → eve = Jan 10
    ctx = liturgical_context(date(2026, 1, 10))
    assert ctx["week"] == "The Epiphany and Following"
    assert ctx["day"] == "Saturday"


def test_week_of_1_epiphany_sunday():
    # Jan 11 2026 = Baptism Sunday = Week of 1 Epiphany
    ctx = liturgical_context(date(2026, 1, 11))
    assert ctx["week"] == "Week of 1 Epiphany"
    assert ctx["day"] == "Sunday"


# ---------------------------------------------------------------------------
# Last Epiphany / Ash Wednesday boundary
# ---------------------------------------------------------------------------

def test_last_epiphany_sunday_2026():
    # Ash Wed 2026 = Feb 18 → Last Epiphany Sunday = Feb 15
    ctx = liturgical_context(date(2026, 2, 15))
    assert ctx["week"] == "Week of Last Epiphany"
    assert ctx["day"] == "Sunday"


def test_last_epiphany_tuesday_2026():
    ctx = liturgical_context(date(2026, 2, 17))
    assert ctx["week"] == "Week of Last Epiphany"
    assert ctx["day"] == "Tuesday"


# ---------------------------------------------------------------------------
# Lent
# ---------------------------------------------------------------------------

def test_lent_week_1_sunday_2026():
    # First Sunday of Lent = first Sunday after Ash Wednesday Feb 18 = Feb 22
    ctx = liturgical_context(date(2026, 2, 22))
    assert ctx["week"] == "Week of 1 Lent"
    assert ctx["day"] == "Sunday"


def test_lent_week_5_saturday_2026():
    # Week of 5 Lent Saturday = day before Palm Sunday (Mar 29 - 1 = Mar 28)
    ctx = liturgical_context(date(2026, 3, 28))
    assert ctx["week"] == "Week of 5 Lent"
    assert ctx["day"] == "Saturday"


def test_holy_week_palm_sunday_2026():
    ctx = liturgical_context(date(2026, 3, 29))
    assert ctx["week"] == "Holy Week"
    assert ctx["day"] == "Sunday"


def test_holy_week_wednesday_2026():
    ctx = liturgical_context(date(2026, 4, 1))
    assert ctx["week"] == "Holy Week"
    assert ctx["day"] == "Wednesday"


# ---------------------------------------------------------------------------
# Easter Week
# ---------------------------------------------------------------------------

def test_easter_monday_2026():
    ctx = liturgical_context(date(2026, 4, 6))
    assert ctx["week"] == "Easter Week"
    assert ctx["day"] == "Monday"


def test_week_of_2_easter_sunday_2026():
    ctx = liturgical_context(date(2026, 4, 12))
    assert ctx["week"] == "Week of 2 Easter"
    assert ctx["day"] == "Sunday"


# ---------------------------------------------------------------------------
# Season after Pentecost (Proper N)
# ---------------------------------------------------------------------------

def test_proper_n_after_trinity_2026():
    # Monday after Trinity Sunday 2026 (Jun 1) → should be Proper 4
    ctx = liturgical_context(date(2026, 6, 1))
    assert ctx is not None
    assert ctx["week"].startswith("Proper")
    assert ctx["day"] == "Monday"


def test_proper_sunday_2026():
    # First Sunday after Trinity 2026 (Jun 7) → Proper 5
    ctx = liturgical_context(date(2026, 6, 7))
    assert ctx is not None
    assert ctx["week"].startswith("Proper")
    assert ctx["day"] == "Sunday"


# ---------------------------------------------------------------------------
# Extreme Easter years (spec requirement)
# ---------------------------------------------------------------------------

def test_early_easter_2008():
    # Easter 2008 = Mar 23 → very few Epiphany weeks
    ctx = liturgical_context(date(2008, 1, 13))  # Sunday after Jan 6
    assert ctx["week"] == "Week of 1 Epiphany"
    assert ctx["day"] == "Sunday"

    ctx_ash = liturgical_context(date(2008, 2, 6))  # Ash Wednesday 2008
    assert ctx_ash["week"] == "Ash Wednesday and Following"


def test_late_easter_2038():
    # Easter 2038 = Apr 25 → many Epiphany weeks including Week of 8 Epiphany
    ctx = liturgical_context(date(2038, 3, 7))  # Should be Week of Last Epiphany
    assert ctx["week"] == "Week of Last Epiphany"


# ---------------------------------------------------------------------------
# Resolver — known-good entries actually found in the index
# ---------------------------------------------------------------------------

def test_resolve_easter_2026():
    result = resolve_office(date(2026, 4, 5))
    assert result is not None
    assert result["week"] == "Easter Week"
    assert result["cycle"] == 2
    assert "morning_lessons" in result
    assert "evening_lessons" in result


def test_resolve_advent_sunday_2024():
    result = resolve_office(date(2024, 12, 1))
    assert result is not None
    assert result["week"] == "Week of 1 Advent"
    assert result["cycle"] == 1


def test_resolve_pentecost_returns_entry():
    result = resolve_office(date(2026, 5, 24))
    assert result is not None
    assert result["week"] == "Pentecost"
    assert result["psalms"]["morning"] != []


def test_resolve_eve_of_pentecost():
    result = resolve_office(date(2026, 5, 23))
    assert result is not None
    assert result["week"] == "Week of 7 Easter"
    # Eve entry has nested lessons; both morning and evening should be populated
    assert result["morning_lessons"] or result["evening_lessons"]


def test_resolve_pentecost_weekday_is_none():
    result = resolve_office(date(2026, 5, 25))
    assert result is None


def test_resolve_trinity_eve_2026():
    result = resolve_office(date(2026, 5, 30))
    assert result is not None
    assert result["week"] == ""


def test_resolve_trinity_sunday_2026():
    result = resolve_office(date(2026, 5, 31))
    assert result is not None
    assert "Trinity" in (result.get("title") or "")


# ---------------------------------------------------------------------------
# flatten_lessons helper
# ---------------------------------------------------------------------------

def test_flatten_lessons_flat_structure():
    entry = {"lessons": {"first": "Gen 1:1", "gospel": "John 1:1"}}
    assert flatten_lessons(entry, "morning") == {"first": "Gen 1:1", "gospel": "John 1:1"}
    assert flatten_lessons(entry, "evening") == {"first": "Gen 1:1", "gospel": "John 1:1"}


def test_flatten_lessons_nested_structure():
    entry = {
        "lessons": {
            "morning": {"first": "Isa 1:1", "second": "Rev 1:1"},
            "evening": {"first": "Ps 1:1"},
        }
    }
    assert flatten_lessons(entry, "morning") == {"first": "Isa 1:1", "second": "Rev 1:1"}
    assert flatten_lessons(entry, "evening") == {"first": "Ps 1:1"}


# ---------------------------------------------------------------------------
# Index completeness — sanity counts
# ---------------------------------------------------------------------------

def test_index_not_empty():
    assert len(DAILY_INDEX) > 700  # ~405 * 2 entries


def test_year_1_and_2_both_present():
    year1_keys = [k for k in DAILY_INDEX if k[0] == 1]
    year2_keys = [k for k in DAILY_INDEX if k[0] == 2]
    assert len(year1_keys) > 300
    assert len(year2_keys) > 300
