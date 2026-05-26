"""Load BCP 1979 Collects JSON files into memory at startup."""
import json
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "collects"

_SEASONS_BY_TITLE: dict[str, dict] = {}
_HOLY_DAYS_BY_MONTH_DAY: dict[str, dict] = {}


def load_collects() -> None:
    global _SEASONS_BY_TITLE, _HOLY_DAYS_BY_MONTH_DAY
    _SEASONS_BY_TITLE.clear()
    _HOLY_DAYS_BY_MONTH_DAY.clear()

    for fname in ("seasons.json", "common_saints.json", "various.json"):
        data: list[dict] = json.loads((_DATA_DIR / fname).read_text(encoding="utf-8"))
        for entry in data:
            _SEASONS_BY_TITLE[entry["title"]] = entry

    holy: list[dict] = json.loads((_DATA_DIR / "holy_days.json").read_text(encoding="utf-8"))
    for entry in holy:
        if "day" in entry:
            _HOLY_DAYS_BY_MONTH_DAY[entry["day"]] = entry


def get_by_title(title: str) -> dict | None:
    return _SEASONS_BY_TITLE.get(title)


def get_by_month_day(month_day: str) -> dict | None:
    return _HOLY_DAYS_BY_MONTH_DAY.get(month_day)
