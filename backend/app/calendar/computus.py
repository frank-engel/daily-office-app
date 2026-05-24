"""
Easter computation and derived moveable feast dates for the BCP 1979 liturgical calendar.
"""
from datetime import date, timedelta


def easter_sunday(year: int) -> date:
    """Return Easter Sunday for the given year using the Gregorian algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def ash_wednesday(year: int) -> date:
    return easter_sunday(year) - timedelta(days=46)


def palm_sunday(year: int) -> date:
    return easter_sunday(year) - timedelta(days=7)


def ascension_day(year: int) -> date:
    return easter_sunday(year) + timedelta(days=39)


def pentecost(year: int) -> date:
    return easter_sunday(year) + timedelta(days=49)


def trinity_sunday(year: int) -> date:
    return easter_sunday(year) + timedelta(days=56)


def first_sunday_of_advent(year: int) -> date:
    """Return the First Sunday of Advent for the liturgical year beginning in *year*."""
    nov_30 = date(year, 11, 30)
    dow = nov_30.weekday()  # Mon=0 … Sun=6
    if dow <= 3:
        return nov_30 - timedelta(days=dow + 1)
    else:
        return nov_30 + timedelta(days=6 - dow)


def liturgical_year_cycle(d: date) -> int:
    """Return 1 (Year One) or 2 (Year Two) for the liturgical year containing *d*.

    The liturgical year begins on the First Sunday of Advent.  The cycle is
    determined by the calendar year that Advent Sunday ushers in:
      odd  → Year One
      even → Year Two
    """
    advent = first_sunday_of_advent(d.year)
    if d >= advent:
        # We are in the new liturgical year that leads into d.year + 1
        next_year = d.year + 1
        return 1 if next_year % 2 == 1 else 2
    else:
        # Still in the liturgical year that started in d.year - 1 Advent
        return 1 if d.year % 2 == 1 else 2
