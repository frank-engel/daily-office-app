#!/usr/bin/env python3
"""
Scrape BCP 1979 Collects from bcponline.org and write JSON files that match
the Reuben Lillie lectionary JSON convention.

Pages scraped (traditional + contemporary pairs):
  seasonst/c.html   → seasons.json        (Advent through Season after Pentecost)
  holydayst/c.html  → holy_days.json      (fixed-calendar saints & feasts)
  commont/c.html    → common_saints.json  (Common of Saints)
  varioust/c.html   → various.json        (Various Occasions)

Usage:
    pip install httpx
    python scripts/scrape_collects.py [--output-dir backend/data/collects]
"""

import argparse
import json
import re
import time
from html import unescape
from pathlib import Path

import httpx

BASE = "https://www.bcponline.org/Collects"

PAGES = {
    "seasons":       ("seasonst.html",  "seasonsc.html"),
    "holy_days":     ("holydayst.html", "holydaysc.html"),
    "common_saints": ("commont.html",   "commonc.html"),
    "various":       ("varioust.html",  "variousc.html"),
}

_MONTH_ABBR = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
}

_DATE_RE      = re.compile(r"\((\w+)\s+(\d+)\)")
_TAG_RE       = re.compile(r"<[^>]+>")
_STRONG_RE    = re.compile(r"<(?:strong|b)\b[^>]*>", re.IGNORECASE)
_ENDSTR_RE    = re.compile(r"</(?:strong|b)\s*>", re.IGNORECASE)
_EM_RE        = re.compile(r"<em\b[^>]*>(.*?)</em\s*>", re.DOTALL | re.IGNORECASE)
# "November 30 " or "June 29 " at the very start of collect body text (holy days)
_LEADING_DATE = re.compile(
    r"^(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d+\s+",
    re.IGNORECASE,
)
# Page-navigation text that leaks into the last collect on contemporary pages
_TRAILING_NAV = re.compile(
    r"\s*(?:Preface[^.]*\.)?\s*Collects?:?\s*(?:Traditional|Contemporary)\s*\d*\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(s: str) -> str:
    """Strip HTML tags, decode entities, collapse whitespace."""
    s = unescape(s)
    s = _TAG_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def _normalize_title(title: str) -> str:
    """
    Canonical form for title-matching: ASCII-only, apostrophes stripped,
    lowercase, collapsed spaces.

    Stripping apostrophes is intentional: the traditional and contemporary pages
    on bcponline.org sometimes disagree on apostrophe placement (e.g. "All Saints’
    Day" vs "All Saint’s Day"). Removing them entirely makes those titles match
    without needing per-entry overrides.
    """
    title = title.encode("ascii", errors="ignore").decode("ascii")
    title = title.replace("\x27", "")   # strip ASCII apostrophe
    return re.sub(r"\s+", " ", title).strip().lower()


# Any remaining title discrepancies after normalization can be added here.
# Keys/values must be the output of _normalize_title() (ASCII, no apostrophes, lowercase).
_TITLE_ALIASES: dict = {}


def _extract_date(title: str):
    """
    'Saint Andrew (November 30)' → ('Saint Andrew', 'Nov 30')
    'Ash Wednesday'              → ('Ash Wednesday', None)
    """
    m = _DATE_RE.search(title)
    if not m:
        return title, None
    month_full, day = m.group(1), m.group(2)
    abbr = _MONTH_ABBR.get(month_full)
    date_str = f"{abbr} {day}" if abbr else None
    clean = _DATE_RE.sub("", title).strip().rstrip(",").strip()
    return clean, date_str


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_page(html: str) -> list:
    """
    Extract collects from a bcponline.org Collects page.

    Structure on the page:
        <strong>Title</strong>
        Collect body text ... <em>Amen.</em>
        <em>Preface of X</em>
        <strong>Next Title</strong>
        ...

    Returns a list of {"title": str, "text": str, "preface": str | None}.
    """
    bm = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    body = bm.group(1) if bm else html

    parts = _STRONG_RE.split(body)
    collects = []

    for part in parts[1:]:   # first slice is content before any <strong>
        # Title runs up to </strong>
        tm = _ENDSTR_RE.search(part)
        if not tm:
            continue
        title = _clean(part[: tm.start()])
        if not title or len(title) < 3:
            continue

        content = part[tm.end():]

        # Find the last <em>Preface of …</em> in this block
        preface = None
        for em_m in _EM_RE.finditer(content):
            em_text = _clean(em_m.group(1))
            if em_text.lower().startswith("preface"):
                preface = em_text

        # Strip HTML for the collect body
        text = _clean(content)
        # Strip page-navigation junk first — it appears AFTER the preface on the
        # page, so it must be removed before the preface-strip regex can anchor to $
        text = _TRAILING_NAV.sub("", text).strip()
        # Now strip "Preface of X" (± trailing page number) from the end. The
        # preface <em> text bleeds into the body because _clean() strips tags.
        if preface:
            pf_pat = re.escape(preface) + r"(?:\s+\d+)?\s*$"
            text = re.sub(pf_pat, "", text).strip()

        # Skip navigation fragments and headings (too short to be a collect)
        if len(text) < 50:
            continue

        collects.append({"title": title, "text": text, "preface": preface})

    return collects


# ---------------------------------------------------------------------------
# Merge traditional + contemporary
# ---------------------------------------------------------------------------

def merge_collects(trad: list, contemp: list) -> list:
    """
    Pair traditional and contemporary versions by normalized title.
    Preserves traditional ordering; appends any contemporary-only entries.
    Uses _normalize_title() as the match key so minor apostrophe/spacing
    variants (e.g. "All Saints' Day" vs "All Saint's Day") still merge correctly.
    """
    # normalized_key → original title (prefer traditional spelling)
    key_to_title: dict = {}
    trad_map:    dict = {}
    contemp_map: dict = {}

    for c in trad:
        k = _normalize_title(c["title"])
        k = _TITLE_ALIASES.get(k, k)
        trad_map[k] = c
        key_to_title.setdefault(k, c["title"])

    for c in contemp:
        k = _normalize_title(c["title"])
        k = _TITLE_ALIASES.get(k, k)
        contemp_map[k] = c
        key_to_title.setdefault(k, c["title"])

    # Preserve trad order, then append contemp-only
    seen: set = set()
    keys: list = []
    for c in trad + contemp:
        k = _normalize_title(c["title"])
        k = _TITLE_ALIASES.get(k, k)
        if k not in seen:
            keys.append(k)
            seen.add(k)

    result = []
    for k in keys:
        t = trad_map.get(k)
        c = contemp_map.get(k)
        preface = (t or c or {}).get("preface")

        entry = {"title": key_to_title[k]}
        if preface:
            entry["preface"] = preface
        entry["collect"] = {}
        if t:
            entry["collect"]["traditional"] = t["text"]
        if c:
            entry["collect"]["contemporary"] = c["text"]
        result.append(entry)

    return result


def add_holy_day_dates(entries: list) -> list:
    """
    Extract calendar dates for holy days and strip them from collect text.

    The date appears in two places on the bcponline.org page:
      - Parenthetical in the <strong> title: "Saint Andrew (November 30)"  [rare]
      - As leading text in the collect body: "November 30 Almighty God..."  [common]

    We check both, promote to a top-level "day" field in 'Mon DD' format, and
    remove the date string from the collect body so it doesn't pollute the text.
    """
    out = []
    for e in entries:
        entry = {**e}

        # Try title first (parenthetical format)
        clean_title, date = _extract_date(entry["title"])
        entry["title"] = clean_title

        # If not in title, look at leading text in the collect body
        if not date:
            for lang in ("traditional", "contemporary"):
                text = entry.get("collect", {}).get(lang, "")
                m = _LEADING_DATE.match(text)
                if m:
                    raw = m.group(0).strip().split()  # ["November", "30"]
                    if len(raw) == 2:
                        abbr = _MONTH_ABBR.get(raw[0].capitalize())
                        if abbr:
                            date = f"{abbr} {raw[1]}"
                    break

        # Strip the leading date from both collect versions
        if date:
            entry["day"] = date
            for lang in ("traditional", "contemporary"):
                text = entry.get("collect", {}).get(lang, "")
                m = _LEADING_DATE.match(text)
                if m:
                    entry["collect"][lang] = text[m.end():]

        out.append(entry)
    return out


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def fetch(url: str) -> str:
    r = httpx.get(
        url,
        follow_redirects=True,
        timeout=30,
        headers={"User-Agent": "daily-office-app/0.1 (data collection)"},
    )
    r.raise_for_status()
    return r.text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for name, (trad_file, contemp_file) in PAGES.items():
        print(f"  fetching {name} (traditional)...")
        trad_html = fetch(f"{BASE}/{trad_file}")
        time.sleep(1)

        print(f"  fetching {name} (contemporary)...")
        contemp_html = fetch(f"{BASE}/{contemp_file}")
        time.sleep(1)

        trad    = parse_page(trad_html)
        contemp = parse_page(contemp_html)
        merged  = merge_collects(trad, contemp)

        if name == "holy_days":
            merged = add_holy_day_dates(merged)

        out_path = output_dir / f"{name}.json"
        out_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"  -> {len(merged)} collects written to {out_path}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Scrape BCP 1979 Collects from bcponline.org → JSON"
    )
    ap.add_argument(
        "--output-dir",
        default="backend/data/collects",
        type=Path,
        metavar="DIR",
        help="Directory to write JSON files (default: backend/data/collects)",
    )
    args = ap.parse_args()
    main(args.output_dir)
