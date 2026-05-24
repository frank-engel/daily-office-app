"""
Data-quality fixes applied to each lectionary entry before indexing.

Known issues in the source JSON:
  1. "1 Kings" → "1 Kgs" (SBL standard abbreviation)
  2. Rev 21:1–4,–14 → corrected reference in KNOWN_OVERRIDES
  3. Double-encoded en-dash (â€") → U+2013 (not present in current dataset,
     guard kept for safety)
"""
import re

# Reference strings to replace verbatim (resolved ambiguous or malformed refs)
KNOWN_OVERRIDES: dict[str, str] = {
    "Rev 21:1–4,–14": "Rev 21:1–4, 9–14",
}

_BOOK_FIXES = [
    (re.compile(r"\b1 Kings\b"), "1 Kgs"),
]


def _fix_ref(s: str) -> str:
    """Apply known overrides and book-name normalization to a reference string."""
    # Known overrides first (verbatim match)
    if s in KNOWN_OVERRIDES:
        return KNOWN_OVERRIDES[s]
    # Double-encoded en-dash guard
    s = s.replace("â", "–")
    # Book name normalization
    for pattern, replacement in _BOOK_FIXES:
        s = pattern.sub(replacement, s)
    return s


def _normalize_lessons(lessons: dict) -> dict:
    """Recursively normalize all reference strings in a lessons dict."""
    out = {}
    for k, v in lessons.items():
        if isinstance(v, str):
            out[k] = _fix_ref(v)
        elif isinstance(v, dict):
            out[k] = _normalize_lessons(v)
        else:
            out[k] = v
    return out


def normalize_entry(entry: dict) -> dict:
    """Return a normalized copy of a lectionary entry."""
    entry = dict(entry)
    if "lessons" in entry:
        entry["lessons"] = _normalize_lessons(entry["lessons"])
    return entry
