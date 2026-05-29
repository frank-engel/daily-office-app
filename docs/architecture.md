# Architecture

## Overview

The app is a single-process Python FastAPI server. There is no cloud infrastructure
in the MVP — everything runs locally and is accessed from an Android WebView over
`adb reverse`.

```
┌─────────────────────────────────────────────────────────┐
│  Browser / Android WebView  (localhost:8000)            │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP
┌─────────────────────▼───────────────────────────────────┐
│  FastAPI  (uvicorn)                                     │
│                                                         │
│  HTML routes  (Jinja2 + HTMX)                          │
│  ├─ GET /                       ─► index.html           │
│  ├─ GET /office/{date}          ─► office.html          │
│  ├─ GET /full/{date}            ─► office_full.html     │
│  ├─ GET /habits                 ─► habits.html          │
│  └─ GET /partials/office/{date}/{tab}                   │
│       ─► _office_tab.html  (HTMX partial swap)         │
│                                                         │
│  JSON API routes                                        │
│  ├─ /api/office/{date}       ─► Calendar + Lectionary   │
│  │                               + Bible DB + Collects  │
│  ├─ /api/office/{date}/full  ─► Office builder          │
│  │                               + Bible DB             │
│  ├─ /api/bible/{ref}         ─► Reference parser        │
│  │                               + Bible DB             │
│  ├─ /api/psalms/{n}          ─► Bible DB                │
│  └─ /api/habits/*            ─► Habit DB                │
│                                                         │
└──────────┬──────────────┬──────────────────────────────-┘
           │              │
    ┌──────▼──────┐  ┌────▼──────┐
    │  web.sqlite │  │habits.db  │
    │  (KJVA)     │  │           │
    └─────────────┘  └───────────┘
```

## Module map

### `app/calendar/`

| Module | Responsibility |
|---|---|
| `computus.py` | Easter Sunday date — Gregorian algorithm |
| `liturgical_year.py` | Date → `{cycle, season, week, day}` context dict |

`liturgical_year.py` builds a Proper-number lookup table at import time (Proper 1–29
keyed on the nearest Sunday date) and binary-searches it at call time.

### `app/lectionary/`

| Module | Responsibility |
|---|---|
| `loader.py` | Parse JSON files into `DAILY_INDEX` and `HOLY_DAY_INDEX` at startup |
| `normalizer.py` | Fix known data-quality issues in the source JSON |
| `resolver.py` | `resolve_office(date)` — calendar context → lectionary entry |

`DAILY_INDEX` is keyed `(cycle: int, week: str, day: str)`.  
`HOLY_DAY_INDEX` is keyed on `"Dec 25"` / `"Nov 1"` etc.

**Holy day precedence:** `resolver.py` checks `HOLY_DAY_INDEX` before `DAILY_INDEX` so
fixed-calendar saints' days always override ordinary weekday readings. Principal Feasts
(Easter Week, Pentecost, Holy Week, Trinity Sunday) are protected from displacement.

### `app/collects/`

| Module | Responsibility |
|---|---|
| `loader.py` | Load `seasons.json`, `holy_days.json`, `common_saints.json`, `various.json` |
| `resolver.py` | `resolve_collect(date, ctx)` → Collect of the Day dict |

Fixed saints' days are checked first; seasonal collects are matched via a title lookup table.

### `app/bible/`

| Module | Responsibility |
|---|---|
| `book_map.py` | SBL abbreviation → KJVA `book_id` integer |
| `reference_parser.py` | Reference string → list of `VerseRange` objects |
| `db.py` | Async SQLite verse and psalm fetching |

`reference_parser.py` handles all BCP reference formats including multi-section,
cross-chapter, letter-suffixed verses, and parenthetical optionals.

### `app/office/`

| Module | Responsibility |
|---|---|
| `loader.py` | Load `canticles.json`, `opening_sentences.json`, `fixed_texts.json` at startup |
| `canticle_resolver.py` | Date + liturgical context → canticle numbers per BCP table (p. 144–145) |
| `builder.py` | Assemble the ordered block list for full Morning/Evening Prayer |

`builder.py` returns a list of typed blocks (heading, rubric, versicle, canticle, psalm,
lesson, creed, prayer, etc.) that are consumed by `office_full.html` and `/api/office/{date}/full`.

### `app/habits/`

| Module | Responsibility |
|---|---|
| `db.py` | `habits.sqlite` CRUD — `mark_complete`, `unmark`, `is_complete`, `get_completions` |

### `app/api/`

FastAPI `APIRouter` modules. Each file is a thin HTTP layer — no business logic.
`office.py` also exports `build_office_context()`, a shared coroutine used by both
the JSON API route and the HTML page routes in `main.py`.

### `app/templates/`

Jinja2 templates served by the HTML routes in `main.py`.

| Template | Role |
|---|---|
| `base.html` | Shared shell — nav bar, Tailwind + HTMX CDN, `<main>` wrapper |
| `index.html` | Home page — "Open Today's Office" link |
| `office.html` | Daily Office page — date header, collect, prev/next nav, Morning/Evening tab bar |
| `_office_tab.html` | Partial — psalms + lessons for one time-of-day; returned by `/partials/` and `{% include %}`d on initial load |
| `office_full.html` | Full Office page — complete rendered Morning/Evening Prayer service |
| `_office_blocks.html` | Partial — renders the typed block list from `builder.py` |
| `habits.html` | 30-day habit completion grid with HTMX toggles |
| `_habit_toggle.html` | Partial — single habit pill/button; returned by the toggle endpoint |
| `404.html` | Not-found error page (styled, extends `base.html`) |
| `500.html` | Server error page (styled, extends `base.html`) |

## Data flow for `/api/office/{date}`

```
1. liturgical_context(date)
      → Easter math → season / week / day / cycle

2. HOLY_DAY_INDEX.get("Nov 30")           ← check fixed feast first
   or DAILY_INDEX[(cycle, week, day)]     ← fall back to ordinary day
      → raw lectionary entry (JSON)

3. resolve_collect(date, ctx)
      → HOLY_DAY_INDEX (collects) or seasonal title lookup
      → {"title", "preface", "traditional", "contemporary"}

4. flatten_lessons(entry, "morning")
   flatten_lessons(entry, "evening")
      → {"first": "Isa 1:1–9", "second": "2 Pet 3:1–10", "gospel": "Matt 25:1–13"}

5. parse_reference("Isa 1:1–9")
      → [VerseRange(book="Isa", start_chapter=1, start_verse=1, end_chapter=1, end_verse=9)]

6. KJVA_verses WHERE book_id=23 AND chapter=1 AND verse BETWEEN 1 AND 9
      → [{book, chapter, verse, text}, ...]

7a. JSON route  → OfficeResponse (Pydantic model) → JSON response
7b. HTML route  → build_office_context() dict → Jinja2 office.html → HTML response
                   HTMX tab click → /partials/office/{date}/{tab} → _office_tab.html fragment
```

## Key design decisions

**Why SQLite (not Postgres)?**  
MVP is a personal device app. SQLite is zero-config, ships in the standard library,
and handles the read-heavy Bible lookup workload without issue.

**Why aiosqlite?**  
FastAPI is async. Blocking SQLite I/O on the event loop would serialize requests.
`aiosqlite` wraps SQLite in a thread pool so async/await syntax works correctly.

**Why KJVA (not WEB)?**  
The original architecture specified the World English Bible (WEB), but the
scrollmapper database repository reorganized its layout and no longer ships a
`sqlite/web.db` file. KJVA is the only single public-domain SQLite file that covers
the full Anglican canon including Apocrypha (80 books). The code is database-agnostic
via `book_map.py`; switching translations in the future only requires updating that
file and the table name constants in `db.py`.

**Why accept both hyphen and en-dash in references?**  
The BCP lectionary JSON source uses en-dashes internally. Rather than requiring callers
to know that, `parse_reference()` normalizes ASCII hyphens to en-dashes on entry. The
internal representation stays consistent; the public API stays ergonomic.

**Why in-memory lectionary index?**  
The JSON files are ~400 KB total and loaded once at startup. In-memory dict lookup
is O(1) and far simpler than an additional SQLite table for 810 lectionary entries.

**Why no ORM?**  
The Bible DB schema is read-only and the query patterns are simple range lookups.
Raw `aiosqlite` is less dependency surface and is faster for this access pattern.

**Holy day interrupt design**  
The BCP rubric is: Principal Feasts > Sundays > Holy Days > ordinary days. The resolver
implements this as: check `HOLY_DAY_INDEX` first for ordinary-day contexts; block the
check for protected weeks (Easter Week, Pentecost, Holy Week, Trinity Sunday) so
Principal Feasts can never be displaced by a coincident fixed feast (e.g. Visitation on
May 31 when Trinity Sunday falls on that date).

## Future seams (post-MVP)

- `app/api/reflection.py` — `POST /api/reflection/{date}` returns HTTP 501. The
  `reflection: null` field in `OfficeResponse` is reserved for a Claude API integration.
- `user_id` in habits schema is nullable from day one — ready for Cognito post-MVP.
- `liturgical_context()` returns a rich dict (season, color, collect ref) intended as
  future Claude API system-prompt context.
