"""
Resolve canticle assignments for Morning and Evening Prayer per BCP 1979 pp. 144-145.
All numbers refer to Rite II canticles.
"""
from datetime import date

from app.calendar.liturgical_year import WEEKDAY_NAMES

# ── Morning Prayer — after OT (first) lesson ─────────────────────────────────
_MP_AFTER_OT: dict[str, int] = {
    "Sunday":    16,
    "Monday":     9,
    "Tuesday":   13,
    "Wednesday": 11,
    "Thursday":   8,
    "Friday":    10,
    "Saturday":  12,
}

# (day, season) overrides for MP after OT
_MP_AFTER_OT_OVERRIDES: dict[tuple[str, str], int] = {
    ("Sunday",    "Advent"):  11,
    ("Sunday",    "Lent"):    14,
    ("Sunday",    "Easter"):   8,
    ("Wednesday", "Lent"):    14,
    ("Friday",    "Lent"):    14,
}

# ── Morning Prayer — after NT (second/gospel) lesson ─────────────────────────
_MP_AFTER_NT: dict[str, int] = {
    "Sunday":    21,
    "Monday":    19,
    "Tuesday":   18,
    "Wednesday": 16,
    "Thursday":  20,
    "Friday":    18,
    "Saturday":  19,
}

# (day, season) overrides for MP after NT
_MP_AFTER_NT_OVERRIDES: dict[tuple[str, str], int] = {
    ("Sunday",   "Advent"): 16,
    ("Sunday",   "Lent"):   16,
    ("Thursday", "Advent"): 19,
    ("Thursday", "Lent"):   19,
}

# ── Evening Prayer — after first (OT) lesson ─────────────────────────────────
_EP_AFTER_OT: dict[str, int] = {
    "Sunday":    15,
    "Monday":     8,
    "Tuesday":   10,
    "Wednesday": 12,
    "Thursday":  11,
    "Friday":    13,
    "Saturday":   9,
}

# ── Evening Prayer — after second (NT/Gospel) lesson ─────────────────────────
_EP_AFTER_NT: dict[str, int] = {
    "Sunday":    17,
    "Monday":    17,
    "Tuesday":   15,
    "Wednesday": 17,
    "Thursday":  15,
    "Friday":    17,
    "Saturday":  15,
}

_STANDARD_DAYS = frozenset(WEEKDAY_NAMES)


def _dow(d: date, lit_ctx: dict) -> str:
    """
    Return the liturgical day-of-week name for canticle table lookup.
    Special day labels (e.g. 'Dec 25', 'Jan 6') fall back to the date's actual weekday.
    """
    day = lit_ctx.get("day", "")
    if day in _STANDARD_DAYS:
        return day
    return WEEKDAY_NAMES[d.weekday()]


def resolve_canticles(
    d: date,
    time_of_day: str,
    lit_ctx: dict,
    is_major_feast: bool,
) -> dict[str, int]:
    """
    Return {"after_ot": int, "after_nt": int} — Rite II canticle numbers.

    is_major_feast: True for fixed-calendar principal feasts (Christmas, Epiphany,
    All Saints, etc.) as well as Easter Sunday and Pentecost.
    """
    season = lit_ctx.get("season", "")
    dow = _dow(d, lit_ctx)

    if time_of_day == "morning":
        if is_major_feast:
            return {"after_ot": 16, "after_nt": 21}
        after_ot = _MP_AFTER_OT_OVERRIDES.get((dow, season), _MP_AFTER_OT.get(dow, 9))
        after_nt = _MP_AFTER_NT_OVERRIDES.get((dow, season), _MP_AFTER_NT.get(dow, 21))
        return {"after_ot": after_ot, "after_nt": after_nt}

    else:  # evening
        if is_major_feast:
            return {"after_ot": 15, "after_nt": 17}
        after_ot = _EP_AFTER_OT.get(dow, 15)
        after_nt = _EP_AFTER_NT.get(dow, 17)
        return {"after_ot": after_ot, "after_nt": after_nt}
