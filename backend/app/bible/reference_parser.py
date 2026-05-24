"""
Parse BCP lectionary Bible references into structured verse-range queries.

Supported formats (range separator is en-dash U+2013, not ASCII hyphen):
  "Isa 1:1–9"               simple range
  "Gal 3:23–29; 4:4–7"      multi-section, semicolon-separated
  "Isa 5:8–12, 18–23"       multi-range, same chapter
  "2 Pet 2:1–10a"           letter-suffixed verse (strip a/b)
  "Luke 20:41–21:4"         chapter-spanning range
  "John 17:1–11(12–26)"     parenthetical optional suffix
  "Isa 42:(1–9)10–17"       parenthetical optional prefix
  "Rev 21:1–4,–14"          ambiguous — handled via KNOWN_OVERRIDES
"""
from __future__ import annotations

import re
from dataclasses import dataclass

EN_DASH = "–"

# Pre-built overrides for genuinely ambiguous references.
# Maps the raw reference string to a list of (start_chapter, start_verse, end_chapter, end_verse).
KNOWN_OVERRIDES: dict[str, list[tuple[str, list[tuple[int, int, int, int]]]]] = {
    "Rev 21:1–4,–14": [("Rev", [(21, 1, 21, 4), (21, 9, 21, 14)])],
}


@dataclass
class VerseRange:
    book: str
    start_chapter: int
    start_verse: int
    end_chapter: int
    end_verse: int


def parse_reference(ref: str) -> list[VerseRange]:
    """
    Parse a lectionary reference string into a list of VerseRange objects.

    Returns an empty list if the reference cannot be parsed.
    """
    ref = ref.strip()

    # Check known overrides first
    if ref in KNOWN_OVERRIDES:
        result = []
        for book, ranges in KNOWN_OVERRIDES[ref]:
            for sc, sv, ec, ev in ranges:
                result.append(VerseRange(book, sc, sv, ec, ev))
        return result

    # Strip parenthetical optional sections:
    #   "John 17:1–11(12–26)"  → "John 17:1–11"
    #   "Isa 42:(1–9)10–17"   → "Isa 42:10–17"
    ref = re.sub(r'\([^)]*\)', '', ref).strip()
    # Clean up any stray commas/dashes left at boundaries
    ref = re.sub(r',\s*$', '', ref).strip()

    # Split on semicolons into sections
    sections = [s.strip() for s in ref.split(';')]

    result: list[VerseRange] = []
    current_book: str | None = None
    current_chapter: int | None = None

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Try to extract a book name + chapter from the section
        # Book names: optional digit prefix, space-separated word(s)
        book_match = re.match(
            r'^(\d\s+[A-Z][a-zA-Z]+|[A-Z][a-zA-Z]+(?:\s+of\s+[A-Z][a-zA-Z]+)?)\s+(\d+):(.+)$',
            section,
        )

        if book_match:
            current_book = book_match.group(1).strip()
            current_chapter = int(book_match.group(2))
            ranges_str = book_match.group(3)
        elif current_book and re.match(r'^\d+:(.+)$', section):
            # Continuation with new chapter (e.g., "4:4–7" after "Gal 3:23–29")
            chap_match = re.match(r'^(\d+):(.+)$', section)
            current_chapter = int(chap_match.group(1))
            ranges_str = chap_match.group(2)
        else:
            # No book/chapter context — skip
            continue

        # Parse the ranges_str, which may be:
        #   "1–9"          single range
        #   "8–12, 18–23"  multiple ranges same chapter
        #   "20:41–21:4"   chapter-spanning (whole ref was already parsed above)
        for rng in _split_ranges(ranges_str):
            vr = _parse_single_range(current_book, current_chapter, rng)
            if vr:
                result.append(vr)
                # Update current_chapter to the end chapter for continuation
                current_chapter = vr.end_chapter

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_ranges(ranges_str: str) -> list[str]:
    """Split a ranges string on commas, but only when the comma is not part of a chapter-verse ref."""
    # Simple split on ", " — handles "8–12, 18–23"
    parts = [p.strip() for p in ranges_str.split(',')]
    return [p for p in parts if p]


def _strip_letter_suffix(s: str) -> str:
    """Remove trailing a/b letter from verse number string."""
    return re.sub(r'[ab]$', '', s.strip())


def _parse_single_range(book: str, chapter: int, rng: str) -> VerseRange | None:
    """
    Parse a single range string given known book and base chapter.

    Handles:
      "1–9"        → chapter:1 to chapter:9
      "20:41–21:4" → 20:41 to 21:4 (chapter embedded in range)
      "10a"        → chapter:10 to chapter:10
    """
    rng = rng.strip()
    if not rng:
        return None

    # Chapter-spanning with both chapters explicit: "20:41–21:4"
    cross_match = re.match(
        rf'^(\d+):(\d+[ab]?){EN_DASH}(\d+):(\d+[ab]?)$', rng
    )
    if cross_match:
        sc = int(cross_match.group(1))
        sv = int(_strip_letter_suffix(cross_match.group(2)))
        ec = int(cross_match.group(3))
        ev = int(_strip_letter_suffix(cross_match.group(4)))
        return VerseRange(book, sc, sv, ec, ev)

    # Chapter-spanning where start chapter is already known: "41–21:4"
    partial_cross = re.match(rf'^(\d+[ab]?){EN_DASH}(\d+):(\d+[ab]?)$', rng)
    if partial_cross:
        sv = int(_strip_letter_suffix(partial_cross.group(1)))
        ec = int(partial_cross.group(2))
        ev = int(_strip_letter_suffix(partial_cross.group(3)))
        return VerseRange(book, chapter, sv, ec, ev)

    # Simple range: "1–9" or "10a–15b"
    simple_match = re.match(rf'^(\d+[ab]?){EN_DASH}(\d+[ab]?)$', rng)
    if simple_match:
        sv = int(_strip_letter_suffix(simple_match.group(1)))
        ev = int(_strip_letter_suffix(simple_match.group(2)))
        return VerseRange(book, chapter, sv, chapter, ev)

    # Single verse: "10" or "10a"
    single_match = re.match(r'^(\d+[ab]?)$', rng)
    if single_match:
        v = int(_strip_letter_suffix(single_match.group(1)))
        return VerseRange(book, chapter, v, chapter, v)

    return None
