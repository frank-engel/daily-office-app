"""
Liturgical calendar engine: given a date, determine the BCP 1979 season,
week name, day name, and year cycle for Daily Office lectionary lookup.
"""
from datetime import date, timedelta
from .computus import easter_sunday, first_sunday_of_advent

WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
]

MONTH_ABBREVS = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def _day_name(d: date) -> str:
    return WEEKDAY_NAMES[d.weekday()]


def _next_sunday_after(d: date) -> date:
    """First Sunday strictly after d."""
    days = (7 - ((d.weekday() + 1) % 7)) % 7
    if days == 0:
        days = 7
    return d + timedelta(days=days)


def _sunday_nearest(target: date) -> date:
    """Sunday closest in date to target (ties go to the previous Sunday)."""
    dow = (target.weekday() + 1) % 7  # Sun=0, Mon=1, ..., Sat=6
    prev = target - timedelta(days=dow)
    nxt = prev + timedelta(days=7)
    return prev if dow <= 3 else nxt


def _proper_sundays(easter_year: int) -> list[tuple[int, date]]:
    """Return [(proper_num, sunday_date), ...] for Proper 1-29."""
    may11 = date(easter_year, 5, 11)
    p1 = _sunday_nearest(may11)
    return [(n, p1 + timedelta(days=(n - 1) * 7)) for n in range(1, 30)]


def liturgical_context(d: date) -> dict | None:
    """
    Return the liturgical week context for date *d*:
        {"week": str, "day": str, "cycle": int, "season": str}

    Returns None for dates that fall outside the covered lectionary range.
    """
    # Determine which Easter year governs this date
    advent_this = first_sunday_of_advent(d.year)
    if d >= advent_this:
        easter_year = d.year + 1
        advent_start = advent_this
    else:
        easter_year = d.year
        advent_start = first_sunday_of_advent(d.year - 1)

    cycle = 1 if easter_year % 2 == 1 else 2

    # Key moveable dates
    easter = easter_sunday(easter_year)
    ash = easter - timedelta(days=46)
    pent = easter + timedelta(days=49)
    trinity = easter + timedelta(days=56)

    # Key fixed dates within this liturgical year
    christmas = date(easter_year - 1, 12, 25)
    jan6 = date(easter_year, 1, 6)

    # ── ADVENT ─────────────────────────────────────────────────────────────
    if advent_start <= d < christmas:
        n = (d - advent_start).days // 7 + 1
        # Dec 24 (Christmas Eve) has its own lectionary entry keyed "Dec 24",
        # not a generic Saturday entry — use the month-day name when it applies.
        day = "Dec 24" if (d.month == 12 and d.day == 24) else _day_name(d)
        return {"week": f"Week of {n} Advent", "day": day,
                "cycle": cycle, "season": "Advent"}

    # ── CHRISTMAS (Dec 25 – Jan 5) ─────────────────────────────────────────
    if christmas <= d < jan6:
        if d.weekday() == 6:  # Sunday
            day = "Sunday"
        elif d.month == 12:
            day = f"Dec {d.day}"
        else:
            day = f"Jan {d.day}"
        return {"week": "Christmas Day and Following", "day": day,
                "cycle": cycle, "season": "Christmas"}

    # Baptism Sunday = first Sunday strictly after Jan 6
    baptism_sunday = _next_sunday_after(jan6)
    epiphany_eve = baptism_sunday - timedelta(days=1)

    # ── EPIPHANY AND FOLLOWING (Jan 6 – eve of Baptism Sunday) ────────────
    if jan6 <= d <= epiphany_eve:
        day = "Saturday" if d == epiphany_eve else f"Jan {d.day}"
        return {"week": "The Epiphany and Following", "day": day,
                "cycle": cycle, "season": "Epiphany"}

    # ── WEEKS OF EPIPHANY ──────────────────────────────────────────────────
    # Ash Wednesday is always a Wednesday; the Sunday before it = last Epiphany
    last_epi_sunday = ash - timedelta(days=3)

    if baptism_sunday <= d < ash:
        if d >= last_epi_sunday:
            week = "Week of Last Epiphany"
        else:
            n = (d - baptism_sunday).days // 7 + 1
            week = f"Week of {n} Epiphany"
        return {"week": week, "day": _day_name(d), "cycle": cycle, "season": "Epiphany"}

    # ── ASH WEDNESDAY AND FOLLOWING ────────────────────────────────────────
    lent1_sunday = _next_sunday_after(ash)
    if ash <= d < lent1_sunday:
        return {"week": "Ash Wednesday and Following", "day": _day_name(d),
                "cycle": cycle, "season": "Lent"}

    # ── WEEKS OF LENT ──────────────────────────────────────────────────────
    palm_sunday = easter - timedelta(days=7)
    if lent1_sunday <= d < palm_sunday:
        n = (d - lent1_sunday).days // 7 + 1
        return {"week": f"Week of {n} Lent", "day": _day_name(d),
                "cycle": cycle, "season": "Lent"}

    # ── HOLY WEEK ──────────────────────────────────────────────────────────
    if palm_sunday <= d < easter:
        return {"week": "Holy Week", "day": _day_name(d), "cycle": cycle, "season": "Lent"}

    # ── EASTER WEEK ────────────────────────────────────────────────────────
    easter2 = easter + timedelta(days=7)
    if easter <= d < easter2:
        return {"week": "Easter Week", "day": _day_name(d), "cycle": cycle, "season": "Easter"}

    # ── WEEKS OF EASTER 2-7 ────────────────────────────────────────────────
    if easter2 <= d < pent:
        n = (d - easter2).days // 7 + 2
        return {"week": f"Week of {n} Easter", "day": _day_name(d),
                "cycle": cycle, "season": "Easter"}

    # ── PENTECOST SUNDAY ────────────────────────────────────────────────────
    if d == pent:
        return {"week": "Pentecost", "day": "Sunday", "cycle": cycle, "season": "Easter"}

    trinity_eve = trinity - timedelta(days=1)

    # ── EVE OF TRINITY SUNDAY ──────────────────────────────────────────────
    if d == trinity_eve:
        return {"week": "", "day": "Saturday", "cycle": cycle,
                "season": "Pentecost", "title": "Eve of Trinity Sunday"}

    # ── TRINITY SUNDAY ─────────────────────────────────────────────────────
    if d == trinity:
        return {"week": "", "day": "Sunday", "cycle": cycle,
                "season": "Pentecost",
                "title": "The First Sunday after Pentecost: Trinity Sunday"}

    # ── SEASON AFTER PENTECOST (Proper N) ─────────────────────────────────
    proper_list = _proper_sundays(easter_year)
    for i, (n, sun) in enumerate(proper_list):
        next_sun = proper_list[i + 1][1] if i + 1 < len(proper_list) else date(9999, 1, 1)
        if sun <= d < next_sun:
            return {"week": f"Proper {n}", "day": _day_name(d),
                    "cycle": cycle, "season": "Pentecost"}

    return None


def liturgical_context_rich(d: date) -> dict | None:
    """Extends liturgical_context with liturgical color and collect key."""
    ctx = liturgical_context(d)
    if ctx is None:
        return None
    season = ctx.get("season", "")
    color = _liturgical_color(season, ctx.get("week", ""), ctx.get("day", ""))
    return {**ctx, "color": color, "collect_ref": ctx.get("week", "")}


def _liturgical_color(season: str, week: str, day: str) -> str:
    if season == "Advent":
        return "blue"
    if season == "Christmas" or season == "Epiphany":
        return "white"
    if season == "Lent":
        return "purple"
    if week == "Holy Week":
        return "red"
    if season == "Easter":
        return "white"
    if week == "Pentecost":
        return "red"
    if season == "Pentecost":
        return "green"
    return "green"
