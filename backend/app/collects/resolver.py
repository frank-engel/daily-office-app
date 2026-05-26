"""Resolve a date + liturgical context to the BCP 1979 Collect of the Day."""
from datetime import date

from .loader import get_by_month_day, get_by_title

_MONTH_ABBREVS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

# Day-specific collects within a week (week, weekday-name) → seasons.json title
_DAY_SPECIFIC: dict[tuple[str, str], str] = {
    ("Holy Week", "Sunday"):    "Sunday of the Passion: Palm Sunday",
    ("Holy Week", "Monday"):    "Monday in Holy Week",
    ("Holy Week", "Tuesday"):   "Tuesday in Holy Week",
    ("Holy Week", "Wednesday"): "Wednesday in Holy Week",
    ("Holy Week", "Thursday"):  "Maundy Thursday",
    ("Holy Week", "Friday"):    "Good Friday",
    ("Holy Week", "Saturday"):  "Holy Saturday",
    ("Easter Week", "Sunday"):    "Easter Day",
    ("Easter Week", "Monday"):    "Monday in Easter Week",
    ("Easter Week", "Tuesday"):   "Tuesday in Easter Week",
    ("Easter Week", "Wednesday"): "Wednesday in Easter Week",
    ("Easter Week", "Thursday"):  "Thursday in Easter Week",
    ("Easter Week", "Friday"):    "Friday in Easter Week",
    ("Easter Week", "Saturday"):  "Saturday in Easter Week",
    # Ascension Day is always Thursday of Week of 6 Easter (Easter + 39)
    ("Week of 6 Easter", "Thursday"): "Ascension Day",
}

# Whole-week collects: any day of the week uses this collect
_WEEK_TO_TITLE: dict[str, str] = {
    "Week of 1 Advent":         "First Sunday of Advent",
    "Week of 2 Advent":         "Second Sunday of Advent",
    "Week of 3 Advent":         "Third Sunday of Advent",
    "Week of 4 Advent":         "Fourth Sunday of Advent",
    "The Epiphany and Following": "The Epiphany",
    "Week of 1 Epiphany":  "First Sunday after the Epiphany: The Baptism of our Lord",
    "Week of 2 Epiphany":  "Second Sunday after the Epiphany",
    "Week of 3 Epiphany":  "Third Sunday after the Epiphany",
    "Week of 4 Epiphany":  "Fourth Sunday after the Epiphany",
    "Week of 5 Epiphany":  "Fifth Sunday after the Epiphany",
    "Week of 6 Epiphany":  "Sixth Sunday after the Epiphany",
    "Week of 7 Epiphany":  "Seventh Sunday after the Epiphany",
    "Week of 8 Epiphany":  "Eighth Sunday after the Epiphany",
    "Week of Last Epiphany": "Last Sunday after the Epiphany",
    "Ash Wednesday and Following": "Ash Wednesday",
    "Week of 1 Lent": "First Sunday in Lent",
    "Week of 2 Lent": "Second Sunday in Lent",
    "Week of 3 Lent": "Third Sunday in Lent",
    "Week of 4 Lent": "Fourth Sunday in Lent",
    "Week of 5 Lent": "Fifth Sunday in Lent",
    "Week of 2 Easter": "Second Sunday of Easter",
    "Week of 3 Easter": "Third Sunday of Easter",
    "Week of 4 Easter": "Fourth Sunday of Easter",
    "Week of 5 Easter": "Fifth Sunday of Easter",
    "Week of 6 Easter": "Sixth Sunday of Easter",
    "Week of 7 Easter": "Seventh Sunday of Easter: The Sunday after Ascension Day",
    "Pentecost": "The Day of Pentecost: Whitsunday",
}


def _resolve_title(d: date, ctx: dict) -> str | None:
    """Map a date + liturgical context to a seasons.json title."""
    week = ctx.get("week", "")
    day = ctx.get("day", "")

    # Trinity Sunday and its eve
    title_override = ctx.get("title", "")
    if title_override in (
        "The First Sunday after Pentecost: Trinity Sunday",
        "Eve of Trinity Sunday",
    ):
        return "First Sunday after Pentecost: Trinity Sunday"

    # Day-specific collects (Holy Week, Easter Week, Ascension)
    if (week, day) in _DAY_SPECIFIC:
        return _DAY_SPECIFIC[(week, day)]

    # Christmas season: date-aware because multiple named days share the same week/day keys
    if week == "Christmas Day and Following":
        if d.month == 12 and d.day == 25:
            return "The Nativity of Our Lord: Christmas Day"
        if d.month == 1 and d.day == 1:
            return "The Holy Name"
        if day == "Sunday":
            # First Sunday = Dec 26-31; Second Sunday = Jan 2-5
            return (
                "First Sunday after Christmas Day" if d.month == 12
                else "Second Sunday after Christmas Day"
            )
        # Remaining weekdays (Dec 26-31 not in holy_days, Jan 2-5) use Christmas collect
        return "The Nativity of Our Lord: Christmas Day"

    # Propers directly match seasons.json titles
    if week.startswith("Proper "):
        return week

    return _WEEK_TO_TITLE.get(week)


def _format(entry: dict) -> dict:
    return {
        "title": entry["title"],
        "preface": entry.get("preface", ""),
        "traditional": entry["collect"]["traditional"],
        "contemporary": entry["collect"]["contemporary"],
    }


def resolve_collect(d: date, ctx: dict) -> dict | None:
    """Return the Collect of the Day for *d*, or None if not resolvable."""
    # Fixed saints' days and feasts (holy_days.json) take precedence
    month_day = f"{_MONTH_ABBREVS[d.month]} {d.day}"
    holy = get_by_month_day(month_day)
    if holy:
        return _format(holy)

    title = _resolve_title(d, ctx)
    if not title:
        return None
    entry = get_by_title(title)
    return _format(entry) if entry else None
