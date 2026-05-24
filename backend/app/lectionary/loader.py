"""
Load the BCP 1979 lectionary JSON files into in-memory indexes at startup.

Indexes built:
  DAILY_INDEX  : Dict[(cycle: int, week: str, day: str), entry]
                 Keyed on Year 1/2, week name, and weekday name (or date string).
  HOLY_DAY_INDEX: Dict[str, entry]
                 Keyed on the entry's "day" field, e.g. "Nov 30", "Dec 25".
"""
import json
import logging
from pathlib import Path
from typing import TypeAlias

from .normalizer import normalize_entry

log = logging.getLogger(__name__)

# Type aliases
DailyKey: TypeAlias = tuple[int, str, str]   # (cycle, week, day)
DailyIndex: TypeAlias = dict[DailyKey, dict]
HolyDayIndex: TypeAlias = dict[str, dict]

# Populated by load_lectionary()
DAILY_INDEX: DailyIndex = {}
HOLY_DAY_INDEX: HolyDayIndex = {}

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "readings"

_YEAR_FILES = [
    (_DATA_DIR / "year_1.json", 1),
    (_DATA_DIR / "year_2.json", 2),
]


def _cycle_from_year_string(year_str: str) -> int:
    return 1 if "One" in year_str else 2


def load_lectionary() -> None:
    """Load all lectionary JSON files and populate DAILY_INDEX and HOLY_DAY_INDEX."""
    DAILY_INDEX.clear()
    HOLY_DAY_INDEX.clear()

    # Year 1 and Year 2 daily readings
    for path, cycle in _YEAR_FILES:
        if not path.exists():
            log.error("Missing lectionary file: %s", path)
            continue
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
        dupes = 0
        for raw in entries:
            entry = normalize_entry(raw)
            week = entry.get("week", "")
            day = entry.get("day", "")
            if not day:
                log.warning("Entry missing 'day' field, skipping: %s", entry.get("title"))
                continue
            key: DailyKey = (cycle, week, day)
            if key in DAILY_INDEX:
                dupes += 1
                log.debug("Duplicate key %s — keeping first", key)
            else:
                DAILY_INDEX[key] = entry
        log.info("Loaded %s: %d entries (%d dupes skipped)", path.name, len(entries), dupes)

    # Holy days (fixed-calendar feasts)
    holy_path = _DATA_DIR / "holy_days.json"
    if holy_path.exists():
        with open(holy_path, encoding="utf-8") as f:
            entries = json.load(f)
        for raw in entries:
            entry = normalize_entry(raw)
            day_key = entry.get("day", "")
            if day_key:
                HOLY_DAY_INDEX[day_key] = entry
        log.info("Loaded %s: %d holy days", holy_path.name, len(HOLY_DAY_INDEX))

    log.info(
        "Lectionary loaded: %d daily entries, %d holy days",
        len(DAILY_INDEX),
        len(HOLY_DAY_INDEX),
    )
