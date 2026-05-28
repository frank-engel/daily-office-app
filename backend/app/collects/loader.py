"""Load BCP 1979 Collects JSON files into memory at startup."""
import json
import re
from pathlib import Path

_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "collects"

_SEASONS_BY_TITLE: dict[str, dict] = {}
_HOLY_DAYS_BY_MONTH_DAY: dict[str, dict] = {}

# Mid-text page-number artifacts injected by the PDF scraper, e.g. "228 Collects: Contemporary"
_PAGE_REF = re.compile(r'\s*\d{3}\s+Collects:\s+(?:Traditional|Contemporary)\s*')

# Leading rubric text that precedes the actual prayer in the scraped data
_LEADING_RUBRIC = re.compile(
    r'^(?:'
    # Fixed-day date prefix: "December 25 ", "January 1 ", "January 6 "
    r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+'
    # Proper rubric: "The Sunday closest to May 25 " / "Week of the Sunday closest to May 11 "
    r'|(?:Week of the |The )?Sunday closest to \w+\s+\d+\s+'
    # Multi-sentence Christmas Sunday instruction
    r'|This Sunday takes precedence[^.]+\.[^.]+\.\s+'
    # Page-reference lead: "The Proper Liturgy for this day is on page 264 . "
    r'|The [^.]+?is on page \d+\s+\.\s+'
    # Pentecost vigil instruction (long multi-sentence block ending with "follows the Sermon. ")
    r'|When a Vigil of Pentecost.*?follows the Sermon\.\s+'
    # Last Sunday after the Epiphany
    r'|This Proper is always used on the Sunday before Ash Wednesday\.?\s+'
    # Various Occasions day-suitability note: "Especially suitable for Thursdays "
    r'|Especially suitable for \w+\s+'
    # Various Occasions usage note + section header: "For use on ... I. For fruitful seasons "
    r'|For use on the traditional days or at other times [IVX]+\. For [^A-Z]+'
    r')'
)


def _clean_collect(text: str) -> str:
    # 1. Remove mid-text page number artifacts (they break sentences mid-word)
    text = _PAGE_REF.sub(' ', text)
    # 2. Truncate at first "Amen." — strips trailing rubric, alt collects, preface notes
    amen_idx = text.find('Amen.')
    if amen_idx != -1:
        text = text[:amen_idx + 5]
    # 3. Strip leading rubric text before the prayer begins
    text = _LEADING_RUBRIC.sub('', text)
    return text.strip()


def load_collects() -> None:
    global _SEASONS_BY_TITLE, _HOLY_DAYS_BY_MONTH_DAY
    _SEASONS_BY_TITLE.clear()
    _HOLY_DAYS_BY_MONTH_DAY.clear()

    for fname in ("seasons.json", "common_saints.json", "various.json"):
        data: list[dict] = json.loads((_DATA_DIR / fname).read_text(encoding="utf-8"))
        for entry in data:
            for rite in ("traditional", "contemporary"):
                if rite in entry.get("collect", {}):
                    entry["collect"][rite] = _clean_collect(entry["collect"][rite])
            _SEASONS_BY_TITLE[entry["title"]] = entry

    holy: list[dict] = json.loads((_DATA_DIR / "holy_days.json").read_text(encoding="utf-8"))
    for entry in holy:
        for rite in ("traditional", "contemporary"):
            if rite in entry.get("collect", {}):
                entry["collect"][rite] = _clean_collect(entry["collect"][rite])
        if "day" in entry:
            _HOLY_DAYS_BY_MONTH_DAY[entry["day"]] = entry


def get_by_title(title: str) -> dict | None:
    return _SEASONS_BY_TITLE.get(title)


def get_by_month_day(month_day: str) -> dict | None:
    return _HOLY_DAYS_BY_MONTH_DAY.get(month_day)
