"""
Resolve a calendar date to a lectionary entry.

Lookup order:
  1. Fixed-calendar feasts (HOLY_DAY_INDEX) — saint's days always take precedence.
  2. Daily lectionary index keyed on (cycle, week, day).
"""
from datetime import date

from app.calendar.liturgical_year import liturgical_context, MONTH_ABBREVS
from .loader import DAILY_INDEX, HOLY_DAY_INDEX

# Weeks that are Principal Feasts or special seasons — fixed saints' days may not
# interrupt these (BCP rubric: Principal Feasts outrank Holy Days).
_PRINCIPAL_FEAST_WEEKS = frozenset({
    "Easter Week",
    "Holy Week",
    "Pentecost",
    "Ash Wednesday and Following",
})


def flatten_lessons(entry: dict, time_of_day: str) -> dict:
    """
    Return the lessons sub-dict for *time_of_day* ("morning" or "evening").

    Handles two shapes found in the data:
      - Flat: {"first": ..., "second": ..., "gospel": ...}
        → same lessons used for both morning and evening.
      - Nested: {"morning": {...}, "evening": {...}}
        → return the sub-dict for the requested time.
    """
    lessons = entry.get("lessons", {})
    if time_of_day in lessons and isinstance(lessons[time_of_day], dict):
        return lessons[time_of_day]
    # Flat structure: return as-is (drop nested keys if any)
    return {k: v for k, v in lessons.items() if k not in ("morning", "evening")}


def resolve_office(d: date) -> dict | None:
    """
    Return a resolved office dict for date *d*, or None if no entry exists.

    Returned shape::

        {
            "date": "2026-04-05",
            "title": str | None,
            "season": str,
            "week": str,
            "cycle": int,
            "psalms": {"morning": [...], "evening": [...]},
            "morning_lessons": {"first": ..., "second": ..., "gospel": ...},
            "evening_lessons": {"first": ..., "second": ...},
        }
    """
    ctx = liturgical_context(d)
    if ctx is None:
        return None

    cycle = ctx["cycle"]
    week = ctx["week"]
    day = ctx["day"]

    # Fixed-calendar feasts take precedence over ordinary weekdays, but Principal
    # Feasts (Easter Week, Pentecost, Trinity Sunday, etc.) outrank holy days.
    month_day = f"{MONTH_ABBREVS[d.month]} {d.day}"
    is_principal = week in _PRINCIPAL_FEAST_WEEKS or "Trinity" in ctx.get("title", "")
    if is_principal:
        entry = DAILY_INDEX.get((cycle, week, day))
    else:
        entry = HOLY_DAY_INDEX.get(month_day) or DAILY_INDEX.get((cycle, week, day))
    if entry is None:
        return None

    psalms = entry.get("psalms", {})
    morning_psalms = psalms.get("morning", [])
    evening_psalms = psalms.get("evening", [])

    # Saturday psalm override: if Dec 29 notes say "use Psalms 23 and 27 on Saturday"
    notes = entry.get("notes", [])
    if notes and d.weekday() == 5:  # Saturday
        for note in notes:
            if "Saturday" in note and "Evening Prayer" in note:
                import re
                psalm_nums = re.findall(r"\d+", note)
                evening_psalms = psalm_nums
                break

    morning_lessons = flatten_lessons(entry, "morning")
    evening_lessons = flatten_lessons(entry, "evening")

    return {
        "date": d.isoformat(),
        "title": entry.get("title"),
        "season": ctx.get("season"),
        "week": week,
        "cycle": cycle,
        "psalms": {
            "morning": morning_psalms,
            "evening": evening_psalms,
        },
        "morning_lessons": morning_lessons,
        "evening_lessons": evening_lessons,
        "reflection": None,
    }
