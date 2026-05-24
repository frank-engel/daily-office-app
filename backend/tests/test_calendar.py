"""
Tests for Easter computation and derived liturgical dates.
Ground-truth values verified against lectionarypage.net.
"""
from datetime import date
import pytest

from app.calendar.computus import (
    easter_sunday,
    ash_wednesday,
    palm_sunday,
    ascension_day,
    pentecost,
    trinity_sunday,
    first_sunday_of_advent,
    liturgical_year_cycle,
)


# ---------------------------------------------------------------------------
# Easter — spot-check a range of years against known values
# ---------------------------------------------------------------------------

EASTER_DATES = [
    (2020, date(2020, 4, 12)),
    (2021, date(2021, 4, 4)),
    (2022, date(2022, 4, 17)),
    (2023, date(2023, 4, 9)),
    (2024, date(2024, 3, 31)),
    (2025, date(2025, 4, 20)),
    (2026, date(2026, 4, 5)),   # known test date from spec
    (2027, date(2027, 3, 28)),
    (2028, date(2028, 4, 16)),
    # extreme years
    (2008, date(2008, 3, 23)),  # early Easter edge case
    (2038, date(2038, 4, 25)),  # late Easter edge case
]


@pytest.mark.parametrize("year,expected", EASTER_DATES)
def test_easter_sunday(year, expected):
    assert easter_sunday(year) == expected


# ---------------------------------------------------------------------------
# Moveable feasts derived from Easter 2026
# ---------------------------------------------------------------------------

def test_ash_wednesday_2026():
    # Easter Apr 5 − 46 days = Feb 18
    assert ash_wednesday(2026) == date(2026, 2, 18)


def test_palm_sunday_2026():
    # Easter Apr 5 − 7 days = Mar 29
    assert palm_sunday(2026) == date(2026, 3, 29)


def test_ascension_2026():
    # Easter Apr 5 + 39 days = May 14
    assert ascension_day(2026) == date(2026, 5, 14)


def test_pentecost_2026():
    # Easter Apr 5 + 49 days = May 24
    assert pentecost(2026) == date(2026, 5, 24)


def test_trinity_sunday_2026():
    # Easter Apr 5 + 56 days = May 31
    assert trinity_sunday(2026) == date(2026, 5, 31)


# ---------------------------------------------------------------------------
# First Sunday of Advent
# ---------------------------------------------------------------------------

def test_advent_2024():
    # Nov 30, 2024 is a Saturday → Dec 1, 2024
    assert first_sunday_of_advent(2024) == date(2024, 12, 1)


def test_advent_2025():
    # Nov 30, 2025 is a Monday → Nov 29, 2025
    assert first_sunday_of_advent(2025) == date(2025, 11, 30)


# ---------------------------------------------------------------------------
# Year cycle — four known-good dates from the spec
# ---------------------------------------------------------------------------

def test_cycle_dec1_2024():
    # 2024-12-01 = First Sunday of Advent → leads into 2025 (odd) → Year One
    assert liturgical_year_cycle(date(2024, 12, 1)) == 1


def test_cycle_feb18_2026():
    # 2026-02-18 = Ash Wednesday 2026 → Year Two
    assert liturgical_year_cycle(date(2026, 2, 18)) == 2


def test_cycle_apr5_2026():
    # 2026-04-05 = Easter Sunday 2026 → Year Two
    assert liturgical_year_cycle(date(2026, 4, 5)) == 2


def test_cycle_may23_2026():
    # 2026-05-23 = Eve of Pentecost → Year Two
    assert liturgical_year_cycle(date(2026, 5, 23)) == 2


def test_cycle_transitions():
    # Day before Advent 2025 (Nov 29, 2025) should still be Year One
    assert liturgical_year_cycle(date(2025, 11, 28)) == 1
    # Advent Sunday itself (Nov 30, 2025) starts Year Two
    assert liturgical_year_cycle(date(2025, 11, 30)) == 2
